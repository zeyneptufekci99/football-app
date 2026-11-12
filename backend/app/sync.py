import argparse
from datetime import datetime

from .api_client import ApiFootballClient, ApiFootballError
from .config import settings
from .db import get_connection


class SyncAlreadyRunning(Exception):
    pass


class SyncTooRecent(Exception):
    pass


def parse_kickoff(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def normalize_fixture(item: dict) -> dict | None:
    """Ham API maçını düzleştirir. Zorunlu alan eksikse None döner (maç atlanır)."""
    fx = item.get("fixture") or {}
    teams = item.get("teams") or {}
    home = teams.get("home") or {}
    away = teams.get("away") or {}
    goals = item.get("goals") or {}
    status = fx.get("status") or {}
    kickoff = parse_kickoff(fx.get("date"))

    if not (fx.get("id") and kickoff and home.get("id") and away.get("id") and status.get("short")):
        return None
    if home["id"] == away["id"]:
        return None

    return {
        "id": fx["id"],
        "round": (item.get("league") or {}).get("round"),
        "kickoff": kickoff,
        "status_short": status["short"],
        "status_long": status.get("long"),
        "home": home,
        "away": away,
        "home_goals": goals.get("home"),
        "away_goals": goals.get("away"),
        "venue_name": (fx.get("venue") or {}).get("name"),
    }


# ---------- senkronizasyona başlamadan önce kontroller ----------

def check_can_start(cur, league_id: int, season: int, force: bool) -> None:
    cur.execute(
        """
        SELECT 1 FROM sync_runs
        WHERE league_id = %s AND season_year = %s AND status = 'running'
          AND started_at > now() - interval '10 minutes'
        """,
        (league_id, season),
    )
    if cur.fetchone():
        raise SyncAlreadyRunning("A sync for this league and season is already running")

    if not force:
        cur.execute(
            """
            SELECT finished_at FROM sync_runs
            WHERE league_id = %s AND season_year = %s AND status = 'success'
              AND finished_at > now() - make_interval(mins => %s)
            ORDER BY id DESC LIMIT 1
            """,
            (league_id, season, settings.min_sync_interval_minutes),
        )
        row = cur.fetchone()
        if row:
            raise SyncTooRecent(
                f"Synced recently (at {row[0]:%Y-%m-%d %H:%M} UTC). "
                f"Cooldown is {settings.min_sync_interval_minutes} minutes; use force to override"
            )


def preflight(league_id: int, season: int, force: bool) -> None:
    """API'den hızlı hata dönebilmek için, işi başlatmadan önce çağrılır."""
    with get_connection(autocommit=True) as conn:
        with conn.cursor() as cur:
            check_can_start(cur, league_id, season, force)


def needs_full_sync(cur, league_id: int, season: int) -> bool:
    """Sezon veritabanında yoksa ya da son tam senkronizasyon eskiyse True."""
    cur.execute(
        """
        SELECT
          NOT EXISTS (SELECT 1 FROM seasons WHERE league_id = %(l)s AND year = %(y)s)
          OR NOT EXISTS (
              SELECT 1 FROM sync_runs
              WHERE league_id = %(l)s AND season_year = %(y)s
                AND status = 'success' AND mode = 'full'
                AND finished_at > now() - make_interval(days => %(d)s)
          )
        """,
        {"l": league_id, "y": season, "d": settings.full_sync_every_days},
    )
    return cur.fetchone()[0]


# ---------- veri çekme adımları ----------

def _sync_league_and_season(conn, client: ApiFootballClient, league_id: int, season: int) -> int:
    leagues = client.get("/leagues", id=league_id, season=season)
    if not leagues:
        raise ApiFootballError(f"League {league_id} not found for season {season}")
    entry = leagues[0]
    league = entry.get("league") or {}
    season_info = next((s for s in entry.get("seasons") or [] if s.get("year") == season), {})

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO leagues (id, name, country, logo, type)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                name = EXCLUDED.name,
                country = COALESCE(EXCLUDED.country, leagues.country),
                logo = COALESCE(EXCLUDED.logo, leagues.logo),
                type = COALESCE(EXCLUDED.type, leagues.type),
                updated_at = now()
            """,
            (league_id, league.get("name") or f"League {league_id}",
             (entry.get("country") or {}).get("name"), league.get("logo"), league.get("type")),
        )
        cur.execute(
            """
            INSERT INTO seasons (league_id, year, start_date, end_date, is_current)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (league_id, year) DO UPDATE SET
                start_date = COALESCE(EXCLUDED.start_date, seasons.start_date),
                end_date = COALESCE(EXCLUDED.end_date, seasons.end_date),
                is_current = EXCLUDED.is_current
            RETURNING id
            """,
            (league_id, season, season_info.get("start"), season_info.get("end"),
             bool(season_info.get("current"))),
        )
        return cur.fetchone()[0]


def _sync_teams(conn, client: ApiFootballClient, league_id: int, season: int) -> tuple[set[int], int]:
    team_ids: set[int] = set()
    with conn.cursor() as cur:
        for item in client.get("/teams", league=league_id, season=season):
            team = item.get("team") or {}
            if not team.get("id") or not team.get("name"):
                continue
            cur.execute(
                """
                INSERT INTO teams (id, name, code, country, logo, venue_name)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    code = COALESCE(EXCLUDED.code, teams.code),
                    country = COALESCE(EXCLUDED.country, teams.country),
                    logo = COALESCE(EXCLUDED.logo, teams.logo),
                    venue_name = COALESCE(EXCLUDED.venue_name, teams.venue_name),
                    updated_at = now()
                """,
                (team["id"], team["name"], team.get("code"), team.get("country"),
                 team.get("logo"), (item.get("venue") or {}).get("name")),
            )
            team_ids.add(team["id"])
    return team_ids, len(team_ids)


def _run(conn, client: ApiFootballClient, run_id: int, league_id: int, season: int, full: bool) -> dict:
    stats = {"teams_upserted": 0, "fixtures_inserted": 0, "fixtures_updated": 0,
             "fixtures_skipped": 0, "mode": "full" if full else "fixtures"}

    if full:
        season_id = _sync_league_and_season(conn, client, league_id, season)
        team_ids, stats["teams_upserted"] = _sync_teams(conn, client, league_id, season)
    else:
        row = conn.execute(
            "SELECT id FROM seasons WHERE league_id = %s AND year = %s", (league_id, season)
        ).fetchone()
        season_id, team_ids = row[0], set()

    # Maçlar (aynı ID iki kez gelirse sonuncusu geçerli)
    fixtures: dict[int, dict] = {}
    for raw in client.get("/fixtures", league=league_id, season=season):
        fx = normalize_fixture(raw)
        if fx is None:
            stats["fixtures_skipped"] += 1
        else:
            fixtures[fx["id"]] = fx

    with conn.cursor() as cur:
        # Maçlarda geçen ama veritabanında olmayan takımlar: mevcut kaydı ezmeden ekle
        for fx in fixtures.values():
            for side in (fx["home"], fx["away"]):
                if side["id"] not in team_ids:
                    cur.execute(
                        "INSERT INTO teams (id, name, logo) VALUES (%s, %s, %s) ON CONFLICT (id) DO NOTHING",
                        (side["id"], side.get("name") or f"Team {side['id']}", side.get("logo")),
                    )
                    team_ids.add(side["id"])

        for tid in team_ids:
            cur.execute(
                "INSERT INTO season_teams (season_id, team_id) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                (season_id, tid),
            )

        # Mevcut maçlarla karşılaştır: yeni -> ekle, değişen -> güncelle + geçmişe yaz
        cur.execute(
            """
            SELECT id, round, kickoff, status_short, status_long, home_team_id, away_team_id,
                   home_goals, away_goals, venue_name
            FROM fixtures WHERE season_id = %s
            """,
            (season_id,),
        )
        existing = {row[0]: row[1:] for row in cur.fetchall()}

        for fx in fixtures.values():
            new = (fx["round"], fx["kickoff"], fx["status_short"], fx["status_long"],
                   fx["home"]["id"], fx["away"]["id"], fx["home_goals"], fx["away_goals"],
                   fx["venue_name"])
            old = existing.get(fx["id"])

            if old is None:
                cur.execute(
                    """
                    INSERT INTO fixtures (id, season_id, round, kickoff, status_short, status_long,
                                          home_team_id, away_team_id, home_goals, away_goals, venue_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (fx["id"], season_id, *new),
                )
                stats["fixtures_inserted"] += 1
            elif old != new:
                # Sıra: round, kickoff, status_short, status_long, home, away, home_goals, away_goals, venue
                tracked_changed = (old[1], old[2], old[6], old[7]) != (new[1], new[2], new[6], new[7])
                cur.execute(
                    """
                    UPDATE fixtures SET round=%s, kickoff=%s, status_short=%s, status_long=%s,
                        home_team_id=%s, away_team_id=%s, home_goals=%s, away_goals=%s,
                        venue_name=%s, updated_at=now()
                    WHERE id=%s
                    """,
                    (*new, fx["id"]),
                )
                if tracked_changed:
                    cur.execute(
                        """
                        INSERT INTO fixture_changes
                            (fixture_id, sync_run_id, old_status, new_status, old_home_goals, new_home_goals,
                             old_away_goals, new_away_goals, old_kickoff, new_kickoff)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (fx["id"], run_id, old[2], new[2], old[6], new[6], old[7], new[7], old[1], new[1]),
                    )
                stats["fixtures_updated"] += 1

    return stats


def sync_league_season(league_id: int, season: int, daily_limit: int | None = None,
                       force: bool = False) -> dict:
    client = ApiFootballClient(daily_limit=daily_limit)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Aynı lig-sezon için kontrol ve kayıt oluşturma tek işlemde, kilit altında
            cur.execute("SELECT pg_advisory_xact_lock(%s, %s)", (league_id, season))
            check_can_start(cur, league_id, season, force)
            full = needs_full_sync(cur, league_id, season)
            cur.execute(
                "INSERT INTO sync_runs (league_id, season_year, mode) VALUES (%s, %s, %s) RETURNING id",
                (league_id, season, "full" if full else "fixtures"),
            )
            run_id = cur.fetchone()[0]
        conn.commit()  # çalışma kaydı, veri yazımı başarısız olsa bile kalır

        try:
            stats = _run(conn, client, run_id, league_id, season, full)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE sync_runs SET status='success', finished_at=now(), api_calls=%s,
                        teams_upserted=%s, fixtures_inserted=%s, fixtures_updated=%s, fixtures_skipped=%s
                    WHERE id=%s
                    """,
                    (client.calls, stats["teams_upserted"], stats["fixtures_inserted"],
                     stats["fixtures_updated"], stats["fixtures_skipped"], run_id),
                )
            conn.commit()
            return {"run_id": run_id, "api_calls": client.calls, **stats}
        except Exception as exc:
            conn.rollback()  # yarım kalan veri yazımını geri al
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE sync_runs SET status='failed', finished_at=now(), api_calls=%s, error_message=%s WHERE id=%s",
                    (client.calls, str(exc)[:1000], run_id),
                )
            conn.commit()
            raise
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync one league season from API-Football")
    parser.add_argument("--league", type=int, required=True, help="API-Football league id (e.g. 203)")
    parser.add_argument("--season", type=int, required=True, help="Season start year (e.g. 2024)")
    parser.add_argument("--force", action="store_true", help="Ignore the cooldown period")
    args = parser.parse_args()

    try:
        print(sync_league_season(args.league, args.season, force=args.force))
    except (SyncAlreadyRunning, SyncTooRecent) as exc:
        print(f"Skipped: {exc}")


if __name__ == "__main__":
    main()
import argparse
from datetime import datetime

from .api_client import ApiFootballClient, ApiFootballError
from .db import get_connection


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


def _run(conn, client: ApiFootballClient, run_id: int, league_id: int, season: int) -> dict:
    stats = {"teams_upserted": 0, "fixtures_inserted": 0, "fixtures_updated": 0, "fixtures_skipped": 0}

    # 1) Lig ve sezon
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
        season_id = cur.fetchone()[0]

    # 2) Takımlar
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
            stats["teams_upserted"] += 1

    # 3) Maçlar (aynı ID iki kez gelirse sonuncusu geçerli)
    fixtures: dict[int, dict] = {}
    for raw in client.get("/fixtures", league=league_id, season=season):
        fx = normalize_fixture(raw)
        if fx is None:
            stats["fixtures_skipped"] += 1
        else:
            fixtures[fx["id"]] = fx

    with conn.cursor() as cur:
        # Maçlarda geçen ama /teams yanıtında olmayan takımlar: mevcut kaydı ezmeden ekle
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

        # 4) Mevcut maçlarla karşılaştır: yeni -> ekle, değişen -> güncelle + geçmişe yaz
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


def sync_league_season(league_id: int, season: int, daily_limit: int | None = None) -> dict:
    client = ApiFootballClient(daily_limit=daily_limit)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO sync_runs (league_id, season_year) VALUES (%s, %s) RETURNING id",
                (league_id, season),
            )
            run_id = cur.fetchone()[0]
        conn.commit()  # çalışma kaydı, veri yazımı başarısız olsa bile kalır

        try:
            stats = _run(conn, client, run_id, league_id, season)
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE sync_runs SET status='success', finished_at=now(),
                        teams_upserted=%s, fixtures_inserted=%s, fixtures_updated=%s, fixtures_skipped=%s
                    WHERE id=%s
                    """,
                    (stats["teams_upserted"], stats["fixtures_inserted"],
                     stats["fixtures_updated"], stats["fixtures_skipped"], run_id),
                )
            conn.commit()
            return {"run_id": run_id, **stats}
        except Exception as exc:
            conn.rollback()  # yarım kalan veri yazımını geri al
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE sync_runs SET status='failed', finished_at=now(), error_message=%s WHERE id=%s",
                    (str(exc)[:1000], run_id),
                )
            conn.commit()
            raise
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync one league season from API-Football")
    parser.add_argument("--league", type=int, required=True, help="API-Football league id (e.g. 203)")
    parser.add_argument("--season", type=int, required=True, help="Season start year (e.g. 2024)")
    args = parser.parse_args()

    result = sync_league_season(args.league, args.season)
    print(result)


if __name__ == "__main__":
    main()
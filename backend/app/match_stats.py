from datetime import datetime, timedelta, timezone

from psycopg.types.json import Jsonb

from .api_client import ApiFootballClient

FINISHED = ("FT", "AET", "PEN")
RETRY_AFTER = timedelta(hours=24)  # "veri yok" cevabı alınan maça bu süre dolmadan tekrar sorulmaz


class FixtureNotFound(Exception):
    pass


def parse_value(value) -> int | float | None:
    """API değerleri sayı, "40%", "0.36" ya da null gelebilir; hepsi sayıya (ya da None'a) çevrilir."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return value
    try:
        number = float(str(value).strip().rstrip("%"))
    except ValueError:
        return None
    return int(number) if number.is_integer() else number


def _load(conn, fixture_id: int, home_id: int, away_id: int) -> dict:
    rows = conn.execute(
        """
        SELECT s.team_id, s.stats, t.name
        FROM fixture_team_stats s JOIN teams t ON t.id = s.team_id
        WHERE s.fixture_id = %s
        """,
        (fixture_id,),
    ).fetchall()
    by_team = {r["team_id"]: {"team_id": r["team_id"], "name": r["name"], "stats": r["stats"]} for r in rows}
    return {"home": by_team.get(home_id), "away": by_team.get(away_id)}


def _store(conn, fixture: dict, data: list[dict]) -> bool:
    """API yanıtını kaydeder. Her iki takım için de anlamlı veri varsa True döner."""
    by_team: dict[int, dict] = {}
    for item in data:
        team_id = (item.get("team") or {}).get("id")
        if team_id not in (fixture["home_team_id"], fixture["away_team_id"]):
            continue
        stats = {
            s["type"]: parse_value(s.get("value"))
            for s in item.get("statistics") or []
            if s.get("type")
        }
        if any(v is not None for v in stats.values()):
            by_team[team_id] = stats

    has_data = len(by_team) == 2  # tek takımın verisi tutarsız sayılır
    conn.execute("DELETE FROM fixture_team_stats WHERE fixture_id = %s", (fixture["id"],))
    if has_data:
        for team_id, stats in by_team.items():
            conn.execute(
                "INSERT INTO fixture_team_stats (fixture_id, team_id, stats) VALUES (%s, %s, %s)",
                (fixture["id"], team_id, Jsonb(stats)),
            )
    conn.execute(
        """
        INSERT INTO fixture_stats_fetches (fixture_id, fetched_at, has_data) VALUES (%s, now(), %s)
        ON CONFLICT (fixture_id) DO UPDATE SET fetched_at = now(), has_data = EXCLUDED.has_data
        """,
        (fixture["id"], has_data),
    )
    return has_data


def get_match_stats(conn, fixture_id: int) -> dict:
    """conn: dict_row kullanan bağlantı. Önbellekte varsa oradan verir, yoksa API'den bir kez çeker."""
    fixture = conn.execute(
        "SELECT id, home_team_id, away_team_id, status_short FROM fixtures WHERE id = %s",
        (fixture_id,),
    ).fetchone()
    if not fixture:
        raise FixtureNotFound(fixture_id)

    def result(available: bool, reason: str | None, fetched_at=None) -> dict:
        teams = _load(conn, fixture_id, fixture["home_team_id"], fixture["away_team_id"]) if available else {"home": None, "away": None}
        return {"fixture_id": fixture_id, "available": available, "reason": reason, "fetched_at": fetched_at, **teams}

    if fixture["status_short"] not in FINISHED:
        return result(False, "not_finished")

    def cached() -> dict | None:
        fetch = conn.execute(
            "SELECT fetched_at, has_data FROM fixture_stats_fetches WHERE fixture_id = %s", (fixture_id,)
        ).fetchone()
        if fetch is None:
            return None
        if fetch["has_data"]:
            return result(True, None, fetch["fetched_at"])
        if datetime.now(timezone.utc) - fetch["fetched_at"] < RETRY_AFTER:
            return result(False, "no_data", fetch["fetched_at"])
        return None  # "veri yok" cevabı eskidi, tekrar sorulabilir

    if (hit := cached()) is not None:
        return hit

    # Aynı maç için eşzamanlı iki istek tek API çağrısına düşsün: kilit al, sonra tekrar bak
    conn.execute("SELECT pg_advisory_xact_lock(2, %s)", (fixture_id,))
    if (hit := cached()) is not None:
        conn.commit()
        return hit

    data = ApiFootballClient().get("/fixtures/statistics", fixture=fixture_id)
    has_data = _store(conn, fixture, data)
    conn.commit()
    return result(has_data, None if has_data else "no_data", datetime.now(timezone.utc))
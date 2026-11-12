import logging
from datetime import date
from typing import Iterator

import psycopg
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from psycopg.rows import dict_row

from .db import get_connection
from .schemas import (
    FixtureOut, LeagueOut, OverviewOut, RecentMatch, StandingRow, SyncRequest, SyncRunOut,
    TeamOut, TeamStats, UsageOut,
)
from .sync import SyncAlreadyRunning, SyncTooRecent, preflight, sync_league_season
from .sync import sync_league_season

log = logging.getLogger("football")
FINISHED = ["FT", "AET", "PEN"]

app = FastAPI(title="Football API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_db() -> Iterator[psycopg.Connection]:
    conn = get_connection()
    conn.row_factory = dict_row
    try:
        yield conn
    finally:
        conn.close()


def require_season(conn: psycopg.Connection, season_id: int) -> None:
    if not conn.execute("SELECT 1 FROM seasons WHERE id = %s", (season_id,)).fetchone():
        raise HTTPException(404, f"Season {season_id} not found")


def ratio(num: float, den: int) -> float | None:
    return round(num / den, 3) if den else None


@app.get("/leagues", response_model=list[LeagueOut])
def list_leagues(conn=Depends(get_db)):
    return conn.execute(
        """
        SELECT l.id, l.name, l.country, l.logo,
               COALESCE(json_agg(json_build_object('id', s.id, 'year', s.year, 'is_current', s.is_current)
                                 ORDER BY s.year DESC) FILTER (WHERE s.id IS NOT NULL), '[]'::json) AS seasons
        FROM leagues l LEFT JOIN seasons s ON s.league_id = l.id
        GROUP BY l.id ORDER BY l.name
        """
    ).fetchall()

@app.get("/seasons/{season_id}/overview", response_model=OverviewOut)
def overview(season_id: int, conn=Depends(get_db)):
    """Genel görünüm: sayılar veritabanındaki maçlardan hesaplanır."""
    s = conn.execute(
        """
        SELECT s.id AS season_id, s.year, l.id AS league_id, l.name AS league_name
        FROM seasons s JOIN leagues l ON l.id = s.league_id WHERE s.id = %s
        """,
        (season_id,),
    ).fetchone()
    if not s:
        raise HTTPException(404, f"Season {season_id} not found")

    c = conn.execute(
        """
        SELECT count(*) AS total,
               count(*) FILTER (WHERE status_short = ANY(%(fin)s)
                                AND home_goals IS NOT NULL AND away_goals IS NOT NULL) AS played,
               COALESCE(sum(home_goals + away_goals) FILTER (
                   WHERE status_short = ANY(%(fin)s)
                     AND home_goals IS NOT NULL AND away_goals IS NOT NULL), 0) AS goals
        FROM fixtures WHERE season_id = %(s)s
        """,
        {"s": season_id, "fin": FINISHED},
    ).fetchone()

    last = conn.execute(
        """
        SELECT status, finished_at FROM sync_runs
        WHERE league_id = %s AND season_year = %s AND status IN ('success', 'failed')
        ORDER BY id DESC LIMIT 1
        """,
        (s["league_id"], s["year"]),
    ).fetchone()
    last_ok = conn.execute(
        """
        SELECT max(finished_at) AS at FROM sync_runs
        WHERE league_id = %s AND season_year = %s AND status = 'success'
        """,
        (s["league_id"], s["year"]),
    ).fetchone()

    return {
        **s,
        "total_fixtures": c["total"],
        "played": c["played"],
        "unfinished": c["total"] - c["played"],
        "total_goals": c["goals"],
        "goals_per_match": ratio(c["goals"], c["played"]),
        "last_sync_at": last_ok["at"],
        "last_sync_status": last["status"] if last else None,
    }

@app.get("/seasons/{season_id}/teams", response_model=list[TeamOut])
def list_teams(season_id: int, conn=Depends(get_db)):
    require_season(conn, season_id)
    return conn.execute(
        """
        SELECT t.id, t.name, t.code, t.logo, t.venue_name
        FROM season_teams st JOIN teams t ON t.id = st.team_id
        WHERE st.season_id = %s ORDER BY t.name
        """,
        (season_id,),
    ).fetchall()


@app.get("/seasons/{season_id}/fixtures", response_model=list[FixtureOut])
def list_fixtures(
    season_id: int,
    team_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    status: str | None = Query(None, description="Örn. FT, NS"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    conn=Depends(get_db),
):
    require_season(conn, season_id)
    where, params = ["f.season_id = %s"], [season_id]
    if team_id:
        where.append("(f.home_team_id = %s OR f.away_team_id = %s)")
        params += [team_id, team_id]
    if date_from:
        where.append("f.kickoff >= %s::date")
        params.append(date_from)
    if date_to:
        where.append("f.kickoff < (%s::date + 1)")
        params.append(date_to)
    if status:
        where.append("f.status_short = %s")
        params.append(status.upper())

    rows = conn.execute(
        f"""
        SELECT f.id, f.round, f.kickoff, f.status_short, f.status_long, f.home_goals, f.away_goals,
               f.venue_name, h.id AS home_id, h.name AS home_name, h.logo AS home_logo,
               a.id AS away_id, a.name AS away_name, a.logo AS away_logo
        FROM fixtures f
        JOIN teams h ON h.id = f.home_team_id
        JOIN teams a ON a.id = f.away_team_id
        WHERE {' AND '.join(where)}
        ORDER BY f.kickoff, f.id
        LIMIT %s OFFSET %s
        """,
        params + [limit, offset],
    ).fetchall()

    return [
        {
            **{k: r[k] for k in ("id", "round", "kickoff", "status_short", "status_long",
                                 "home_goals", "away_goals", "venue_name")},
            "home": {"id": r["home_id"], "name": r["home_name"], "logo": r["home_logo"]},
            "away": {"id": r["away_id"], "name": r["away_name"], "logo": r["away_logo"]},
        }
        for r in rows
    ]


@app.get("/seasons/{season_id}/standings", response_model=list[StandingRow])
def standings(season_id: int, conn=Depends(get_db)):
    """Puan tablosu: tamamlanmış maçlardan hesaplanır (G=3, B=1, M=0)."""
    require_season(conn, season_id)
    rows = conn.execute(
        """
        WITH results AS (
            SELECT home_team_id AS team_id, home_goals AS gf, away_goals AS ga
            FROM fixtures
            WHERE season_id = %(s)s AND status_short = ANY(%(fin)s)
              AND home_goals IS NOT NULL AND away_goals IS NOT NULL
            UNION ALL
            SELECT away_team_id, away_goals, home_goals
            FROM fixtures
            WHERE season_id = %(s)s AND status_short = ANY(%(fin)s)
              AND home_goals IS NOT NULL AND away_goals IS NOT NULL
        ), agg AS (
            SELECT team_id, count(*) AS played,
                   count(*) FILTER (WHERE gf > ga) AS won,
                   count(*) FILTER (WHERE gf = ga) AS drawn,
                   count(*) FILTER (WHERE gf < ga) AS lost,
                   sum(gf) AS gf, sum(ga) AS ga
            FROM results GROUP BY team_id
        )
        SELECT t.id AS team_id, t.name AS team_name, t.logo AS team_logo,
               COALESCE(a.played, 0) AS played, COALESCE(a.won, 0) AS won,
               COALESCE(a.drawn, 0) AS drawn, COALESCE(a.lost, 0) AS lost,
               COALESCE(a.gf, 0) AS goals_for, COALESCE(a.ga, 0) AS goals_against,
               COALESCE(a.gf, 0) - COALESCE(a.ga, 0) AS goal_diff,
               COALESCE(a.won, 0) * 3 + COALESCE(a.drawn, 0) AS points
        FROM season_teams st
        JOIN teams t ON t.id = st.team_id
        LEFT JOIN agg a ON a.team_id = t.id
        WHERE st.season_id = %(s)s
        ORDER BY points DESC, goal_diff DESC, goals_for DESC, t.name
        """,
        {"s": season_id, "fin": FINISHED},
    ).fetchall()
    return [{"rank": i, **r} for i, r in enumerate(rows, start=1)]


@app.get("/seasons/{season_id}/teams/{team_id}/stats", response_model=TeamStats)
def team_stats(season_id: int, team_id: int, conn=Depends(get_db)):
    """Performans metrikleri: veritabanındaki tamamlanmış maçlardan hesaplanır."""
    require_season(conn, season_id)
    team = conn.execute(
        """
        SELECT t.name FROM season_teams st JOIN teams t ON t.id = st.team_id
        WHERE st.season_id = %s AND t.id = %s
        """,
        (season_id, team_id),
    ).fetchone()
    if not team:
        raise HTTPException(404, f"Team {team_id} is not in season {season_id}")

    rows = conn.execute(
        """
        SELECT f.id AS fixture_id, f.kickoff,
               (f.home_team_id = %(t)s) AS is_home,
               CASE WHEN f.home_team_id = %(t)s THEN f.home_goals ELSE f.away_goals END AS gf,
               CASE WHEN f.home_team_id = %(t)s THEN f.away_goals ELSE f.home_goals END AS ga,
               o.name AS opponent
        FROM fixtures f
        JOIN teams o ON o.id = CASE WHEN f.home_team_id = %(t)s THEN f.away_team_id ELSE f.home_team_id END
        WHERE f.season_id = %(s)s
          AND (f.home_team_id = %(t)s OR f.away_team_id = %(t)s)
          AND f.status_short = ANY(%(fin)s)
          AND f.home_goals IS NOT NULL AND f.away_goals IS NOT NULL
        ORDER BY f.kickoff DESC
        """,
        {"s": season_id, "t": team_id, "fin": FINISHED},
    ).fetchall()  # en yeni maç ilk sırada

    matches = []
    for r in rows:
        result = "W" if r["gf"] > r["ga"] else "D" if r["gf"] == r["ga"] else "L"
        matches.append({
            "fixture_id": r["fixture_id"], "kickoff": r["kickoff"], "opponent": r["opponent"],
            "is_home": r["is_home"], "goals_for": r["gf"], "goals_against": r["ga"], "result": result,
        })

    def summarize(ms: list[dict]) -> dict:
        n = len(ms)
        won = sum(m["result"] == "W" for m in ms)
        drawn = sum(m["result"] == "D" for m in ms)
        gf = sum(m["goals_for"] for m in ms)
        ga = sum(m["goals_against"] for m in ms)
        return {"n": n, "won": won, "drawn": drawn, "lost": n - won - drawn, "gf": gf, "ga": ga}

    def split(ms: list[dict]) -> dict:
        t = summarize(ms)
        return {
            "played": t["n"], "won": t["won"], "drawn": t["drawn"], "lost": t["lost"],
            "points": t["won"] * 3 + t["drawn"],
            "win_rate": ratio(t["won"], t["n"]),
            "goals_for_per_match": ratio(t["gf"], t["n"]),
            "goals_against_per_match": ratio(t["ga"], t["n"]),
        }

    total = summarize(matches)
    last5_matches = matches[:5]
    last5 = summarize(last5_matches)

    # Grafik için maç maç birikmiş puan (eskiden yeniye)
    cumulative, progress = 0, []
    for i, m in enumerate(reversed(matches), start=1):
        cumulative += {"W": 3, "D": 1, "L": 0}[m["result"]]
        progress.append({
            "match_no": i, "kickoff": m["kickoff"], "opponent": m["opponent"],
            "cumulative_points": cumulative,
        })

    return {
        "team_id": team_id, "team_name": team["name"], "season_id": season_id,
        "played": total["n"], "won": total["won"], "drawn": total["drawn"], "lost": total["lost"],
        "points": total["won"] * 3 + total["drawn"],
        "win_rate": ratio(total["won"], total["n"]),
        "goals_for": total["gf"], "goals_against": total["ga"],
        "goals_for_per_match": ratio(total["gf"], total["n"]),
        "goals_against_per_match": ratio(total["ga"], total["n"]),
        "form_last_5": "".join(m["result"] for m in reversed(last5_matches)),
        "last_5_win_rate": ratio(last5["won"], last5["n"]),
        "last_5_goals_for_per_match": ratio(last5["gf"], last5["n"]),
        "last_5_goals_against_per_match": ratio(last5["ga"], last5["n"]),
        "last_5_matches": last5_matches,
        "home": split([m for m in matches if m["is_home"]]),
        "away": split([m for m in matches if not m["is_home"]]),
        "points_progress": progress,
    }

def _background_sync(league_id: int, season: int, force: bool) -> None:
    try:
        sync_league_season(league_id, season, force=force)
    except (SyncAlreadyRunning, SyncTooRecent) as exc:
        log.info("Sync skipped: %s", exc)
    except Exception:
        log.exception("Background sync failed (league=%s, season=%s)", league_id, season)


@app.post("/sync", status_code=202)
def trigger_sync(body: SyncRequest, background: BackgroundTasks):
    try:
        preflight(body.league_id, body.season, body.force)
    except SyncAlreadyRunning as exc:
        raise HTTPException(409, str(exc))
    except SyncTooRecent as exc:
        raise HTTPException(409, str(exc))
    background.add_task(_background_sync, body.league_id, body.season, body.force)
    return {"message": "Sync started", "league_id": body.league_id, "season": body.season}

@app.get("/sync/status", response_model=SyncRunOut)
def sync_status(league_id: int | None = None, season: int | None = None, conn=Depends(get_db)):
    """Son senkronizasyon kaydı. league_id ve season verilirse o lig-sezon için, verilmezse genel."""
    where, params = [], []
    if league_id:
        where.append("league_id = %s")
        params.append(league_id)
    if season:
        where.append("season_year = %s")
        params.append(season)
    sql = "SELECT * FROM sync_runs"
    if where:
        sql += " WHERE " + " AND ".join(where)
    row = conn.execute(sql + " ORDER BY id DESC LIMIT 1", params).fetchone()
    if not row:
        raise HTTPException(404, "No sync run found")
    return row

@app.get("/usage", response_model=UsageOut)
def api_usage(conn=Depends(get_db)):
    """Bugünkü API-Football kullanımı (kendi kayıtlarımızdan)."""
    return get_usage(conn)
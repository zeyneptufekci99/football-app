import argparse
import logging
import time

from psycopg.rows import dict_row

from .api_client import DailyBudgetExceeded
from .config import settings
from .db import get_connection
from .sync import SyncAlreadyRunning, SyncTooRecent, sync_league_season

log = logging.getLogger("football.scheduler")

TERMINAL = ["FT", "AET", "PEN", "CANC", "ABD", "AWD", "WO"]
ACTIVE_INTERVAL_MIN = 60     # maç oynanıyor ya da sonuç bekleniyor
IDLE_INTERVAL_MIN = 1440     # yalnızca ileri tarihli maçlar var

PLAN_SQL = """
SELECT l.id AS league_id, l.name AS league_name, s.year,
       p.pending, p.live, p.overdue,
       EXTRACT(EPOCH FROM (now() - ls.last_success)) / 60 AS age_min
FROM seasons s
JOIN leagues l ON l.id = s.league_id
LEFT JOIN LATERAL (
    SELECT count(*) FILTER (WHERE status_short <> ALL(%(t)s)) AS pending,
           count(*) FILTER (WHERE status_short <> ALL(%(t)s)
                            AND kickoff <= now() AND kickoff > now() - interval '4 hours') AS live,
           count(*) FILTER (WHERE status_short <> ALL(%(t)s)
                            AND kickoff <= now() - interval '4 hours'
                            AND kickoff > now() - interval '3 days') AS overdue
    FROM fixtures f WHERE f.season_id = s.id
) p ON true
LEFT JOIN LATERAL (
    SELECT max(finished_at) AS last_success FROM sync_runs r
    WHERE r.league_id = l.id AND r.season_year = s.year AND r.status = 'success'
) ls ON true
ORDER BY l.name, s.year
"""


def plan(ignore_interval: bool = False) -> list[dict]:
    with get_connection(autocommit=True) as conn:
        conn.row_factory = dict_row
        rows = conn.execute(PLAN_SQL, {"t": TERMINAL}).fetchall()

    items = []
    for r in rows:
        if r["pending"] == 0:
            interval, reason = None, "season finished, nothing to update"
        elif r["live"] > 0 or r["overdue"] > 0:
            interval, reason = ACTIVE_INTERVAL_MIN, "matches in progress or results pending"
        else:
            interval, reason = IDLE_INTERVAL_MIN, "only upcoming matches"

        age = r["age_min"]
        due = interval is not None and (ignore_interval or age is None or age >= interval)
        items.append({**r, "interval": interval, "reason": reason, "due": due})
    return items


def tick(dry_run: bool = False, ignore_interval: bool = False) -> None:
    items = plan(ignore_interval)
    for it in items:
        age = "never synced" if it["age_min"] is None else f"synced {it['age_min']:.0f} min ago"
        log.info("%s %s: %s (%s) -> %s", it["league_name"], it["year"], it["reason"], age,
                 "DUE" if it["due"] else "skip")
    if dry_run:
        return

    for it in (i for i in items if i["due"]):
        try:
            result = sync_league_season(it["league_id"], it["year"],
                                        daily_limit=settings.auto_sync_budget, force=True)
            log.info("Synced %s %s: %s", it["league_name"], it["year"], result)
        except DailyBudgetExceeded as exc:
            log.warning("Automatic budget reached, stopping this tick: %s", exc)
            break
        except (SyncAlreadyRunning, SyncTooRecent) as exc:
            log.info("Skipped %s %s: %s", it["league_name"], it["year"], exc)
        except Exception:
            log.exception("Sync failed for %s %s", it["league_name"], it["year"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Automatic sync scheduler")
    parser.add_argument("--once", action="store_true", help="Run a single tick and exit")
    parser.add_argument("--dry-run", action="store_true", help="Only print decisions, make no API calls")
    parser.add_argument("--ignore-interval", action="store_true",
                        help="Treat every season with unfinished matches as due (for testing)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    while True:
        try:
            tick(dry_run=args.dry_run, ignore_interval=args.ignore_interval)
        except Exception:
            log.exception("Scheduler tick failed")
        if args.once:
            return
        time.sleep(settings.scheduler_tick_seconds)


if __name__ == "__main__":
    main()
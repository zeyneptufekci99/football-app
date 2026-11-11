from datetime import datetime, timezone

from .config import settings


def get_usage(conn) -> dict:
    """conn: dict_row kullanan bağlantı."""
    row = conn.execute(
        """
        WITH d AS (SELECT date_trunc('day', now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC' AS start)
        SELECT
          (SELECT count(*) FROM api_requests, d
            WHERE http_status IS NOT NULL AND requested_at >= d.start) AS used_today,
          (SELECT count(*) FROM api_requests, d
            WHERE http_status IS NOT NULL AND NOT ok AND requested_at >= d.start) AS failed_today,
          (SELECT api_remaining FROM api_requests, d
            WHERE api_remaining IS NOT NULL AND requested_at >= d.start
            ORDER BY id DESC LIMIT 1) AS api_reported_remaining,
          (SELECT max(requested_at) FROM api_requests) AS last_request_at,
          (SELECT start + interval '1 day' FROM d) AS resets_at
        """
    ).fetchone()
    limit = settings.daily_request_limit
    return {
        "daily_limit": limit,
        "used_today": row["used_today"],
        "failed_today": row["failed_today"],
        "remaining": max(limit - row["used_today"], 0),
        "api_reported_remaining": row["api_reported_remaining"],
        "last_request_at": row["last_request_at"],
        "resets_at": row["resets_at"].astimezone(timezone.utc) if isinstance(row["resets_at"], datetime) else None,
    }
import json 
from .db import get_connection


QUOTA_LOCK_KEY = 7_000_001
_DAY_START = "date_trunc('day', now() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'"

def count_used(conn) -> int:
    """Bugün kotadan düşmüş sayılan istekler: rezerve edilenler ve tamamlananlar."""
    return conn.execute(
        f"SELECT count(*) FROM api_requests "
        f"WHERE state IN ('reserved', 'completed') AND requested_at >={_DAY_START}"
    ).fetchone()[0]

def reserve(endpoint: str, params: dict, limit: int) -> int | None:
    """Kilit altında say ve slot al. Limit dolduysa None döner (istek atılmamalı).

    Kilit yalnızca sayma ve ekleme sırasında tutulur, HTTP isteği süresince değil."""
    with get_connection() as conn:  # bloktan çıkınca commit edilir ve bağlantı kapanır
        conn.execute("SELECT pg_advisory_xact_lock(%s)", (QUOTA_LOCK_KEY,))
        if count_used(conn) >= limit:
            return None
        row = conn.execute(
            "INSERT INTO api_requests (endpoint, params, ok, state) "
            "VALUES (%s, %s, false, 'reserved') RETURNING id",
            (endpoint, json.dumps(params)),
        ).fetchone()
        return row[0]


def finish(request_id: int, http_status: int | None, ok: bool, remaining :int | None, error: str| None) -> None:
    """İstek gönderildi: kotadan düşmüş kalır""" 
    with get_connection(autocommit=True) as conn:
        conn.execute(
            "UPDATE api_requests SET http_status = %s, ok = %s, api_remaining= %s, error = %s, "
            "state = 'completed' WHERE id = %s",
            (http_status, ok, remaining, error[:500] if error else None, request_id),
        )

def release(request_id: int, error: str | None) -> None:
    """İstek API'ye hiç ulaşmadı: rezervasyon iptal edilir"""

    with get_connection(autocommit=True) as conn:
        conn.execute(
            "UPDATE api_requests SET state = 'released', error = %s WHERE id = %s",
            (error[:500] if error else None, request_id)
        )
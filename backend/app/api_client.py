import json
import logging
import time

import httpx

from . import quota
from .config import settings
from .db import get_connection

MAX_RETRIES = 4
log = logging.getLogger("football.api")


class ApiFootballError(Exception):
    pass


class DailyBudgetExceeded(ApiFootballError):
    pass


def requests_used_today() -> int:
    """Bugün (UTC) API'ye ulaşan istek sayısı. Hata dönenler de kotadan düştüğü için dahil. Rezerve edilenler dahil"""
    with get_connection(autocommit=True) as conn:
        return quota.count_used(conn)



def _to_int(value: str | None) -> int | None:
    try:
        return int(value) if value is not None else None
    except ValueError:
        return None

def _record(fn, *args) -> None:
    """Kota kaydı güncellenmezse isteğin sonucunu bozma. 'reserver' kalır ve sayılmaya devam eder"""
    try: 
        fn(*args)
    except Exception:
        log.warning("Could not update quota record", exc_info=True)


class ApiFootballClient:
    def __init__(self, daily_limit: int | None = None, http_client: httpx.Client | None = None) -> None:
        if not settings.api_football_key:
            raise ApiFootballError("API_FOOTBALL_KEY is not set in .env")
        self.daily_limit = daily_limit or settings.daily_request_limit
        self._http = http_client or  httpx.Client(
            base_url=settings.api_football_base_url,
            headers={"x-apisports-key": settings.api_football_key},
            timeout=30,
        )
        self._last_call = 0.0
        self.requests_remaining: int | None = None
        self.calls = 0

    def _throttle(self) -> None:
        wait = settings.min_request_interval - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()

    def get(self, path: str, **params):
        """GET isteği atar, 'response' alanını döndürür. Her denemeden önce kota rezerve edilir. Rezervasyon yapılmazsa istek atılmaz."""
        for attempt in range(1, MAX_RETRIES + 1):
            self._throttle()
            request_id = quota.reserve(path, params, self.daily_limit)
            if request_id is None:
                raise DailyBudgetExceeded(f"Daily request budget reached limit {self.daily_limit}")
            
            try: 
                resp = self._http.get(path, params=params)
            except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
                _record(quota.release, request_id, str(exc)) #kota iade edilir
                if attempt == MAX_RETRIES:
                    raise ApiFootballError(f"Network error on {path}: {exc}") from exc
                time.sleep(2**attempt)
                continue
            except httpx.TransportError as exc:
                #Gönderildikten sonra sorun çıktığı için kotadan düşmüş sayılır.
                self.calls += 1
                _record(quota.finish, request_id, None, False, None, str(exc))
                if attempt == MAX_RETRIES:
                    raise ApiFootballError(f"Network error on {path}: {exc}" ) from exc
                time.sleep(2**attempt)
                continue

            
            self.calls += 1
            remaining = _to_int(resp.headers.get("x-ratelimit-requests-remaining"))
            self.requests_remaining = remaining

            if resp.status_code == 429 or resp.status_code >= 500:
                _record(quota.finish, request_id, resp.status_code, False, remaining, f"HTTP {resp.status_code}")
                if attempt == MAX_RETRIES:
                    raise ApiFootballError(f"{path} failed with HTTP {resp.status_code}")
                time.sleep(2**attempt)
                continue
            if resp.status_code >= 400:
                _record(quota.finish, request_id, resp.status_code, False, remaining, f"HTTP {resp.status_code}")
                raise ApiFootballError(f"{path} failed with HTTP {resp.status_code}")

            try:
                body = resp.json()
            except ValueError as exc:
                _record(quota.finish, request_id, resp.status_code, False, remaining, "Invalid JSON")
                raise ApiFootballError(f"{path} returned invalid JSON") from exc

            # API-Football hata yokken [] döner, hata varken {"alan": "mesaj"} döner (HTTP 200 ile)
            errors = body.get("errors")
            if errors:
                _record(quota.finish, request_id, resp.status_code, False, remaining, str(errors))
                if isinstance(errors, dict) and "requests" in errors:
                    raise DailyBudgetExceeded(f"API reports daily limit reached: {errors['requests']}")
                if isinstance(errors, dict) and "rateLimit" in errors and attempt < MAX_RETRIES:
                    time.sleep(60)
                    continue
                raise ApiFootballError(f"{path} {params}: {errors}")

            _record(quota.finish, request_id, resp.status_code, True, remaining, None)
            return body.get("response") or []

        raise ApiFootballError(f"{path} failed after {MAX_RETRIES} attempts")
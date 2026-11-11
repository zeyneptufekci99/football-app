import time

import httpx

from .config import settings

MAX_RETRIES = 4


class ApiFootballError(Exception):
    pass


class ApiFootballClient:
    def __init__(self) -> None:
        if not settings.api_football_key:
            raise ApiFootballError("API_FOOTBALL_KEY is not set in .env")
        self._http = httpx.Client(
            base_url=settings.api_football_base_url,
            headers={"x-apisports-key": settings.api_football_key},
            timeout=30,
        )
        self._last_call = 0.0
        self.requests_remaining: str | None = None

    def _throttle(self) -> None:
        wait = settings.min_request_interval - (time.monotonic() - self._last_call)
        if wait > 0:
            time.sleep(wait)
        self._last_call = time.monotonic()

    def get(self, path: str, **params) -> list[dict]:
        """GET isteği atar, 'response' listesini döndürür. Hata durumunda tekrar dener."""
        for attempt in range(1, MAX_RETRIES + 1):
            self._throttle()
            try:
                resp = self._http.get(path, params=params)
            except httpx.TransportError as exc:
                if attempt == MAX_RETRIES:
                    raise ApiFootballError(f"Network error on {path}: {exc}") from exc
                time.sleep(2**attempt)
                continue

            self.requests_remaining = resp.headers.get("x-ratelimit-requests-remaining")

            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt == MAX_RETRIES:
                    raise ApiFootballError(f"{path} failed with HTTP {resp.status_code}")
                time.sleep(2**attempt)
                continue
            if resp.status_code >= 400:
                raise ApiFootballError(f"{path} failed with HTTP {resp.status_code}")

            body = resp.json()
            errors = body.get("errors")
            # API-Football hata yokken [] döner, hata varken {"alan": "mesaj"} döner (HTTP 200 ile)
            if errors:
                if isinstance(errors, dict) and "rateLimit" in errors and attempt < MAX_RETRIES:
                    time.sleep(60)
                    continue
                raise ApiFootballError(f"{path} {params}: {errors}")
            return body.get("response") or []

        raise ApiFootballError(f"{path} failed after {MAX_RETRIES} attempts")
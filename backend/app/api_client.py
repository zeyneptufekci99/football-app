import time
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import settings

MAX_RETRIES = 4


class ApiFootballError(Exception):
    pass


class ApiFootballClient:
    def __init__(self) -> None:
        if not settings.api_football_key:
            raise ApiFootballError("API_FOOTBALL_KEY is not set in .env")
        self._base_url = settings.api_football_base_url.rstrip("/")
        self._headers = {"x-apisports-key": settings.api_football_key}
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
            query = urlencode(params, doseq=True)
            url = f"{self._base_url}/{path.lstrip('/')}"
            if query:
                url = f"{url}?{query}"
            request = Request(url, headers=self._headers)
            try:
                with urlopen(request, timeout=30) as resp:
                    status_code = resp.status
                    headers = resp.headers
                    raw_body = resp.read()
            except HTTPError as exc:
                status_code = exc.code
                headers = exc.headers
                raw_body = b""
            except (URLError, TimeoutError, OSError) as exc:
                if attempt == MAX_RETRIES:
                    raise ApiFootballError(f"Network error on {path}: {exc}") from exc
                time.sleep(2**attempt)
                continue

            self.requests_remaining = headers.get("x-ratelimit-requests-remaining")

            if status_code == 429 or status_code >= 500:
                if attempt == MAX_RETRIES:
                    raise ApiFootballError(f"{path} failed with HTTP {status_code}")
                time.sleep(2**attempt)
                continue
            if status_code >= 400:
                raise ApiFootballError(f"{path} failed with HTTP {status_code}")

            body = json.loads(raw_body)
            errors = body.get("errors")
            # API-Football hata yokken [] döner, hata varken {"alan": "mesaj"} döner (HTTP 200 ile)
            if errors:
                if isinstance(errors, dict) and "rateLimit" in errors and attempt < MAX_RETRIES:
                    time.sleep(60)
                    continue
                raise ApiFootballError(f"{path} {params}: {errors}")
            return body.get("response") or []

        raise ApiFootballError(f"{path} failed after {MAX_RETRIES} attempts")
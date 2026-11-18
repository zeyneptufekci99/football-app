import os
import threading
from pathlib import Path

import httpx
import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import conninfo_to_dict, make_conninfo

from app import quota
from app.api_client import ApiFootballClient, ApiFootballError, DailyBudgetExceeded
from app.config import settings

TEST_URL = os.environ.get("TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(not TEST_URL, reason="TEST_DATABASE_URL is not set")


@pytest.fixture(scope="module")
def test_db():
    info = conninfo_to_dict(TEST_URL)
    name = info["dbname"]
    assert name.endswith("test"), "refusing to run against a database whose name does not end with 'test'"
    admin = make_conninfo(**{**info, "dbname": "postgres"})
    with psycopg.connect(admin, autocommit=True) as c:
        if not c.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone():
            c.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    schema = (Path(__file__).resolve().parents[1] / "schema.sql").read_text(encoding="utf-8")
    with psycopg.connect(TEST_URL, autocommit=True) as c:
        c.execute(schema)
    return TEST_URL


@pytest.fixture(autouse=True)
def clean(test_db, monkeypatch):
    monkeypatch.setattr(settings, "database_url", test_db)
    monkeypatch.setattr(settings, "min_request_interval", 0)
    monkeypatch.setattr(settings, "api_football_key", "test-key")
    monkeypatch.setattr("app.api_client.time.sleep", lambda seconds: None)  # yeniden deneme beklemelerini atla
    with psycopg.connect(test_db, autocommit=True) as c:
        c.execute("TRUNCATE api_requests RESTART IDENTITY")


def seed(n: int, state: str = "completed") -> None:
    with psycopg.connect(settings.database_url, autocommit=True) as c:
        c.execute(
            "INSERT INTO api_requests (endpoint, params, http_status, ok, state) "
            "SELECT '/fixtures', '{}', 200, true, %s FROM generate_series(1, %s)",
            (state, n),
        )


def used() -> int:
    with psycopg.connect(settings.database_url, autocommit=True) as c:
        return quota.count_used(c)


def states() -> dict[str, int]:
    with psycopg.connect(settings.database_url, autocommit=True) as c:
        return dict(c.execute("SELECT state, count(*) FROM api_requests GROUP BY state").fetchall())


def make_client(handler, limit: int = 100) -> ApiFootballClient:
    http = httpx.Client(base_url="http://fake-api", transport=httpx.MockTransport(handler))
    return ApiFootballClient(daily_limit=limit, http_client=http)


def counting_ok_handler(calls: list):
    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(200, json={"errors": [], "response": [{"ok": True}]})
    return handler


def run_concurrently(n: int, limit: int, calls: list) -> list[str]:
    results: list[str] = []
    barrier = threading.Barrier(n)

    def worker(i: int) -> None:
        client = make_client(counting_ok_handler(calls), limit=limit)
        barrier.wait(timeout=30)  # hepsi aynı anda başlasın
        try:
            if i % 2:  # farklı uç noktalar, ligler, sezonlar ve maçlar
                client.get("/fixtures", league=200 + i, season=2022 + i % 3)
            else:
                client.get("/fixtures/statistics", fixture=1_000_000 + i)
            results.append("ok")
        except DailyBudgetExceeded:
            results.append("blocked")
        except Exception as exc:  # beklenmedik hata sessizce kaybolmasın
            results.append(f"error: {exc!r}")

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    return results


def test_only_one_of_many_concurrent_requests_gets_the_last_slot():
    seed(99)
    calls: list = []
    results = run_concurrently(8, limit=100, calls=calls)
    assert results.count("ok") == 1
    assert results.count("blocked") == 7
    assert len(calls) == 1  # dış API'ye yalnızca bir istek gitti
    assert used() == 100


def test_many_concurrent_requests_never_exceed_the_limit():
    calls: list = []
    results = run_concurrently(30, limit=10, calls=calls)
    assert results.count("ok") == 10
    assert results.count("blocked") == 20
    assert len(calls) == 10
    assert used() == 10


def test_scheduler_budget_stops_before_the_manual_budget():
    seed(70)
    calls: list = []
    auto = make_client(counting_ok_handler(calls), limit=70)
    manual = make_client(counting_ok_handler(calls), limit=100)
    with pytest.raises(DailyBudgetExceeded):
        auto.get("/fixtures", league=203, season=2024)
    assert manual.get("/fixtures", league=203, season=2024) == [{"ok": True}]
    assert len(calls) == 1
    assert used() == 71


def test_no_http_request_is_made_when_the_budget_is_exhausted():
    seed(100)
    calls: list = []
    with pytest.raises(DailyBudgetExceeded):
        make_client(counting_ok_handler(calls)).get("/fixtures", league=203, season=2024)
    assert calls == []
    assert used() == 100


def test_successful_request_is_recorded_as_completed():
    calls: list = []
    make_client(counting_ok_handler(calls)).get("/fixtures", league=203, season=2024)
    assert states() == {"completed": 1}


def test_connection_failure_does_not_consume_quota():
    def handler(request):
        raise httpx.ConnectError("connection refused", request=request)

    with pytest.raises(ApiFootballError):
        make_client(handler).get("/fixtures", league=203, season=2024)
    assert used() == 0
    assert states() == {"released": 4}  # 4 deneme, hiçbiri API'ye ulaşmadı


def test_read_timeout_after_sending_still_consumes_quota():
    def handler(request):
        raise httpx.ReadTimeout("slow response", request=request)

    with pytest.raises(ApiFootballError):
        make_client(handler).get("/fixtures", league=203, season=2024)
    assert used() == 4  # istek API'ye ulaşmış olabilir, güvenli tarafta kalınır


def test_http_error_responses_consume_quota():
    def handler(request):
        return httpx.Response(500)

    with pytest.raises(ApiFootballError):
        make_client(handler).get("/fixtures", league=203, season=2024)
    assert used() == 4


def test_reservation_left_behind_by_a_killed_process_still_counts():
    request_id = quota.reserve("/fixtures", {"fixture": 1}, limit=100)
    assert request_id is not None
    # İşlem burada öldü: finish() hiç çağrılmadı
    assert states() == {"reserved": 1}
    assert used() == 1
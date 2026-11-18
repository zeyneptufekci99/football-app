import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


client = TestClient(app)
BODY = {"league_id": 203, "season": 2024, "force": True}

@pytest.fixture(autouse=True)
def admin_token(monkeypatch):
    monkeypatch.setattr(settings, "admin_token", "admin-secret")


def test_force_with_wrong_token_is_forbidden():
    assert client.post("/sync", json=BODY, headers={"X-Admin-Token": "wrong"}).status_code == 403

def test_force_is_disabled_when_no_admin_token_is_configured(monkeypatch):
    monkeypatch.setattr(settings, "admin_token","")
    assert client.post("/sync", json=BODY, headers={"X-Admin-Token": ""}).status_code == 403

def test_force_without_token_is_forbidden():
    assert client.post("/sync", json=BODY).status_code == 403
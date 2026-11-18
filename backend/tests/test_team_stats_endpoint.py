"""GET /seasons/{id}/teams/{id}/stats yanıtını doğrular.

Veritabanı yerine, endpoint'in çalıştırdığı sorguların sonucunu döndüren sahte bir bağlantı kullanılır.
Bu testin kapsamı: yönlendirme, ortak hesaplama fonksiyonunun kullanımı ve yanıt biçimi.
Kapsam dışı: SQL'in kendisi (yalnızca tamamlanmış maçları seçmesi).
"""
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
from app.main import app, get_db

client = TestClient(app)
SEASON_ID, TEAM_ID = 1, 10

# Takımın tamamlanmış 7 maçı, EN YENİ maç ilk sırada (endpoint'in SQL'i bu sırayı verir).
# Her satır: (atılan gol, yenilen gol, iç saha mı, rakip)
MATCHES = [
    (2, 0, True, "Rakip A"),   # galibiyet (iç saha)
    (1, 0, False, "Rakip B"),  # galibiyet (deplasman)
    (1, 1, True, "Rakip C"),   # beraberlik (iç saha)
    (0, 2, False, "Rakip D"),  # mağlubiyet (deplasman)
    (0, 1, True, "Rakip E"),   # mağlubiyet (iç saha)
    (3, 1, False, "Rakip F"),  # galibiyet (deplasman)
    (2, 2, True, "Rakip G"),   # beraberlik (iç saha)
]
# Elle hesap (7 maç):
#   Sonuçlar           : 3 G (A, B, F), 2 B (C, G), 2 M (D, E)
#   Puan               : 3*3 + 2*1 = 11
#   Atılan / yenilen   : 2+1+1+0+0+3+2 = 9  /  0+0+1+2+1+1+2 = 7
#   Son 5 maç (A..E)   : G G B M M. Form eskiden yeniye yazılır: E,D,C,B,A -> "LLDWW"
#   İç saha (A,C,E,G)  : 1 G, 2 B, 1 M -> 5 puan.  Deplasman (B,D,F): 2 G, 0 B, 1 M -> 6 puan
#   Birikmiş puan      : eskiden yeniye G(+1) F(+3) E(0) D(0) C(+1) B(+3) A(+3) -> 1,4,4,4,5,8,11
NEWEST = datetime(2025, 5, 24, 17, 0, tzinfo=timezone.utc)


def db_rows(matches=MATCHES):
    return [
        {
            "fixture_id": 100 + i,
            "kickoff": NEWEST - timedelta(days=7 * i),
            "is_home": home,
            "gf": gf,
            "ga": ga,
            "opponent": opponent,
        }
        for i, (gf, ga, home, opponent) in enumerate(matches)
    ]


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)


class FakeConnection:
    """Endpoint'in çalıştırdığı üç sorguyu, SQL metnindeki tablo adlarından tanır."""

    def __init__(self, rows, team_in_season=True):
        self.rows = rows
        self.team_in_season = team_in_season

    def execute(self, query, params=None):
        if "FROM season_teams" in query:
            return FakeResult([{"name": "Test FC"}] if self.team_in_season else [])
        if "FROM fixtures" in query:
            return FakeResult(self.rows)
        if "FROM seasons" in query:
            return FakeResult([{"exists": 1}])
        raise AssertionError(f"Unexpected query: {query[:80]!r}")


@pytest.fixture
def stats_for():
    def request(rows, team_in_season=True):
        conn = FakeConnection(rows, team_in_season)
        app.dependency_overrides[get_db] = lambda: conn
        return client.get(f"/seasons/{SEASON_ID}/teams/{TEAM_ID}/stats")

    yield request
    app.dependency_overrides.clear()


def test_endpoint_returns_season_totals(stats_for):
    resp = stats_for(db_rows())
    assert resp.status_code == 200
    body = resp.json()
    assert body["team_name"] == "Test FC"
    assert (body["played"], body["won"], body["drawn"], body["lost"]) == (7, 3, 2, 2)
    assert body["points"] == 3 * 3 + 2 * 1
    assert body["win_rate"] == round(3 / 7, 3)  # 3 galibiyet / 7 maç
    assert (body["goals_for"], body["goals_against"]) == (9, 7)
    assert body["goals_for_per_match"] == round(9 / 7, 3)
    assert body["goals_against_per_match"] == round(7 / 7, 3)


def test_endpoint_returns_form_and_rates_for_the_last_five_matches(stats_for):
    body = stats_for(db_rows()).json()
    assert body["form_last_5"] == "LLDWW"
    assert body["last_5_win_rate"] == round(2 / 5, 3)  # son 5 maçta 2 galibiyet
    assert body["last_5_goals_for_per_match"] == round((2 + 1 + 1 + 0 + 0) / 5, 3)
    assert body["last_5_goals_against_per_match"] == round((0 + 0 + 1 + 2 + 1) / 5, 3)
    last5 = body["last_5_matches"]
    assert [m["opponent"] for m in last5] == ["Rakip A", "Rakip B", "Rakip C", "Rakip D", "Rakip E"]
    assert [m["result"] for m in last5] == ["W", "W", "D", "L", "L"]


def test_endpoint_splits_home_and_away(stats_for):
    body = stats_for(db_rows()).json()
    home, away = body["home"], body["away"]
    assert (home["played"], home["won"], home["drawn"], home["lost"], home["points"]) == (4, 1, 2, 1, 5)
    assert (away["played"], away["won"], away["drawn"], away["lost"], away["points"]) == (3, 2, 0, 1, 6)
    assert away["win_rate"] == round(2 / 3, 3)
    assert home["played"] + away["played"] == body["played"]
    assert home["points"] + away["points"] == body["points"]


def test_endpoint_returns_cumulative_points_ending_at_the_season_total(stats_for):
    body = stats_for(db_rows()).json()
    progress = [p["cumulative_points"] for p in body["points_progress"]]
    assert progress == [1, 4, 4, 4, 5, 8, 11]
    assert progress[-1] == body["points"]


def test_endpoint_with_no_finished_matches_returns_empty_stats(stats_for):
    body = stats_for([]).json()
    assert body["played"] == 0 and body["points"] == 0
    assert body["win_rate"] is None
    assert body["form_last_5"] == ""
    assert body["points_progress"] == []
    assert body["home"]["played"] == 0 and body["away"]["played"] == 0


def test_endpoint_returns_404_when_team_is_not_in_the_season(stats_for):
    assert stats_for(db_rows(), team_in_season=False).status_code == 404


def test_endpoint_delegates_to_the_shared_calculation(stats_for, monkeypatch):
    seen = []
    real = main_module.compute_team_stats

    def spy(rows):
        seen.append(rows)
        return real(rows)

    monkeypatch.setattr(main_module, "compute_team_stats", spy)
    rows = db_rows()
    assert stats_for(rows).status_code == 200
    assert seen == [rows]  
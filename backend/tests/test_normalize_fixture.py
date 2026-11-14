import copy

import pytest

from app.sync import normalize_fixture

SAMPLE = {
    "fixture": {
        "id": 1000001,
        "date": "2025-05-24T17:00:00+00:00",
        "status": {"short": "FT", "long": "Match Finished"},
        "venue": {"name": "Test Stadium"},
    },
    "league": {"round": "Regular Season - 36"},
    "teams": {
        "home": {"id": 10, "name": "Home FC", "logo": "h.png"},
        "away": {"id": 20, "name": "Away FC", "logo": "a.png"},
    },
    "goals": {"home": 2, "away": 1},
}


def make(**changes):
    """SAMPLE'ın bir kopyasını üretir; 'a.b.c': değer biçiminde alanlar değiştirilir."""
    item = copy.deepcopy(SAMPLE)
    for path, value in changes.items():
        *parents, last = path.split("__")
        target = item
        for key in parents:
            target = target[key]
        target[last] = value
    return item


def test_valid_finished_fixture_is_flattened():
    fx = normalize_fixture(SAMPLE)
    assert fx["id"] == 1000001
    assert fx["round"] == "Regular Season - 36"
    assert fx["status_short"] == "FT"
    assert fx["home"]["id"] == 10 and fx["away"]["id"] == 20
    assert (fx["home_goals"], fx["away_goals"]) == (2, 1)
    assert fx["venue_name"] == "Test Stadium"
    assert fx["kickoff"].year == 2025 and fx["kickoff"].tzinfo is not None


def test_unplayed_fixture_keeps_null_goals():
    fx = normalize_fixture(make(fixture__status={"short": "NS", "long": "Not Started"}, goals={"home": None, "away": None}))
    assert fx is not None
    assert fx["home_goals"] is None and fx["away_goals"] is None
    assert fx["status_short"] == "NS"


def test_missing_optional_fields_do_not_break_normalization():
    item = make(fixture__venue=None)
    item["league"] = {}
    fx = normalize_fixture(item)
    assert fx is not None
    assert fx["venue_name"] is None and fx["round"] is None


@pytest.mark.parametrize(
    "broken",
    [
        make(fixture__id=None),
        make(fixture__date=None),
        make(fixture__date="not-a-date"),
        make(fixture__status={}),
        make(teams__home={"id": None, "name": "Home FC"}),
        make(teams__away={}),
        make(teams__away={"id": 10, "name": "Same Team"}),  # ev sahibi ve deplasman aynı takım
        {},
    ],
)
def test_fixtures_missing_required_data_are_skipped(broken):
    assert normalize_fixture(broken) is None
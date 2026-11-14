from datetime import datetime, timezone

from app.stats import compute_team_stats

# En yeni maç ilk sırada. (atılan, yenilen, iç saha mı)
#  0: 2-0 G  iç saha     3: 0-2 M  deplasman    6: 2-2 B  iç saha
#  1: 1-0 G  deplasman   4: 0-1 M  iç saha
#  2: 1-1 B  iç saha     5: 3-1 G  deplasman
RESULTS = [
    (2, 0, True),
    (1, 0, False),
    (1, 1, True),
    (0, 2, False),
    (0, 1, True),
    (3, 1, False),
    (2, 2, True),
]


def make_rows(results=RESULTS):
    rows = []
    for i, (gf, ga, home) in enumerate(results):
        rows.append({
            "fixture_id": 100 + i,
            "kickoff": datetime(2025, 1, 28 - i, tzinfo=timezone.utc),  # i büyüdükçe eski
            "is_home": home,
            "gf": gf,
            "ga": ga,
            "opponent": f"Opp {i}",
        })
    return rows


def test_empty_season_returns_zeros_and_no_rates():
    stats = compute_team_stats([])
    assert stats["played"] == 0 and stats["points"] == 0
    assert stats["win_rate"] is None
    assert stats["goals_for_per_match"] is None
    assert stats["form_last_5"] == ""
    assert stats["points_progress"] == []


def test_totals_win_rate_and_goal_averages():
    stats = compute_team_stats(make_rows())
    assert (stats["played"], stats["won"], stats["drawn"], stats["lost"]) == (7, 3, 2, 2)
    assert stats["points"] == 11  # 3*3 + 2
    assert stats["win_rate"] == 0.429  # 3/7
    assert (stats["goals_for"], stats["goals_against"]) == (9, 7)
    assert stats["goals_for_per_match"] == 1.286  # 9/7
    assert stats["goals_against_per_match"] == 1.0  # 7/7


def test_form_uses_only_last_five_matches_oldest_to_newest():
    stats = compute_team_stats(make_rows())
    # Son 5 maç (yeniden eskiye): G G B M M -> gösterim eskiden yeniye, en sağ en yeni
    assert stats["form_last_5"] == "LLDWW"
    assert len(stats["last_5_matches"]) == 5
    assert stats["last_5_matches"][0]["fixture_id"] == 100  # en yeni maç ilk sırada


def test_last_five_rates_ignore_older_matches():
    stats = compute_team_stats(make_rows())
    assert stats["last_5_win_rate"] == 0.4  # 2/5
    assert stats["last_5_goals_for_per_match"] == 0.8  # (2+1+1+0+0)/5
    assert stats["last_5_goals_against_per_match"] == 0.8  # (0+0+1+2+1)/5


def test_fewer_than_five_matches_uses_what_exists():
    stats = compute_team_stats(make_rows(RESULTS[:2]))
    assert stats["form_last_5"] == "WW"
    assert stats["last_5_win_rate"] == 1.0
    assert len(stats["last_5_matches"]) == 2


def test_home_and_away_split_adds_up_to_total():
    stats = compute_team_stats(make_rows())
    home, away = stats["home"], stats["away"]
    assert (home["played"], home["won"], home["drawn"], home["lost"], home["points"]) == (4, 1, 2, 1, 5)
    assert (away["played"], away["won"], away["drawn"], away["lost"], away["points"]) == (3, 2, 0, 1, 6)
    assert home["played"] + away["played"] == stats["played"]
    assert home["points"] + away["points"] == stats["points"]


def test_points_progress_is_cumulative_and_ends_at_total_points():
    stats = compute_team_stats(make_rows())
    progress = stats["points_progress"]
    assert [p["match_no"] for p in progress] == list(range(1, 8))
    # Eskiden yeniye: B(1) G(4) M(4) M(4) B(5) G(8) G(11)
    assert [p["cumulative_points"] for p in progress] == [1, 4, 4, 4, 5, 8, 11]
    assert progress[-1]["cumulative_points"] == stats["points"]
    assert progress[0]["kickoff"] < progress[-1]["kickoff"]
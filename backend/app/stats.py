POINTS = {"W": 3, "D": 1, "L": 0}


def ratio(num: float, den: int) -> float | None:
    return round(num / den, 3) if den else None


def result_of(goals_for: int, goals_against: int) -> str:
    if goals_for > goals_against:
        return "W"
    return "D" if goals_for == goals_against else "L"


def _summarize(matches: list[dict]) -> dict:
    n = len(matches)
    won = sum(m["result"] == "W" for m in matches)
    drawn = sum(m["result"] == "D" for m in matches)
    return {
        "n": n,
        "won": won,
        "drawn": drawn,
        "lost": n - won - drawn,
        "gf": sum(m["goals_for"] for m in matches),
        "ga": sum(m["goals_against"] for m in matches),
    }


def _split(matches: list[dict]) -> dict:
    t = _summarize(matches)
    return {
        "played": t["n"], "won": t["won"], "drawn": t["drawn"], "lost": t["lost"],
        "points": t["won"] * 3 + t["drawn"],
        "win_rate": ratio(t["won"], t["n"]),
        "goals_for_per_match": ratio(t["gf"], t["n"]),
        "goals_against_per_match": ratio(t["ga"], t["n"]),
    }


def compute_team_stats(rows: list[dict]) -> dict:
    """Bir takımın tamamlanmış maçlarından performans metriklerini hesaplar.

    rows: EN YENİ maç ilk sırada. Her satır: fixture_id, kickoff, is_home, gf, ga, opponent.
    """
    matches = [
        {
            "fixture_id": r["fixture_id"], "kickoff": r["kickoff"], "opponent": r["opponent"],
            "is_home": r["is_home"], "goals_for": r["gf"], "goals_against": r["ga"],
            "result": result_of(r["gf"], r["ga"]),
        }
        for r in rows
    ]

    total = _summarize(matches)
    last5_matches = matches[:5]
    last5 = _summarize(last5_matches)

    # Grafik için maç maç birikmiş puan (eskiden yeniye)
    cumulative, progress = 0, []
    for i, m in enumerate(reversed(matches), start=1):
        cumulative += POINTS[m["result"]]
        progress.append({
            "match_no": i, "kickoff": m["kickoff"], "opponent": m["opponent"],
            "cumulative_points": cumulative,
        })

    return {
        "played": total["n"], "won": total["won"], "drawn": total["drawn"], "lost": total["lost"],
        "points": total["won"] * 3 + total["drawn"],
        "win_rate": ratio(total["won"], total["n"]),
        "goals_for": total["gf"], "goals_against": total["ga"],
        "goals_for_per_match": ratio(total["gf"], total["n"]),
        "goals_against_per_match": ratio(total["ga"], total["n"]),
        # Son 5 maç, eskiden yeniye: en sağdaki harf en son oynanan maç
        "form_last_5": "".join(m["result"] for m in reversed(last5_matches)),
        "last_5_win_rate": ratio(last5["won"], last5["n"]),
        "last_5_goals_for_per_match": ratio(last5["gf"], last5["n"]),
        "last_5_goals_against_per_match": ratio(last5["ga"], last5["n"]),
        "last_5_matches": last5_matches,
        "home": _split([m for m in matches if m["is_home"]]),
        "away": _split([m for m in matches if not m["is_home"]]),
        "points_progress": progress,
    }
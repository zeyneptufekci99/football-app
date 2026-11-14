import pytest

from app.match_stats import parse_value


@pytest.mark.parametrize(
    "raw, expected",
    [
        (5, 5),
        (0, 0),
        ("40%", 40),
        ("82%", 82),
        ("0.36", 0.36),
        ("2.10", 2.1),
        (" 55% ", 55),
        (None, None),
        ("", None),
        ("n/a", None),
    ],
)
def test_parse_value_converts_api_values_to_numbers(raw, expected):
    assert parse_value(raw) == expected


def test_parse_value_percentage_becomes_integer():
    result = parse_value("40%")
    assert result == 40
    assert isinstance(result, int)
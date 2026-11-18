"""Tests for the deterministic constraint checks (no LLM, no internet)."""

import pytest

from scout.models import Constraints, Paper


def paper(year, citations):
    return Paper(paper_id="W1", title="t", authors=[], year=year, citation_count=citations,
                 citation_source="test", url=None)


@pytest.mark.parametrize("op, expected", [
    ("after", (2023, None)),    # "after 2022" means 2023 or later
    ("from", (2022, None)),
    ("before", (None, 2021)),   # "before 2022" means 2021 or earlier
    ("until", (None, 2022)),
    ("in", (2022, 2022)),
    ("any", (None, None)),
])
def test_year_range(op, expected):
    assert Constraints(topic="x", year_op=op, year=2022).year_range() == expected


@pytest.mark.parametrize("op, expected", [
    ("at_least", (500, None)),
    ("more_than", (501, None)),   # "more than 500" does not include 500
    ("at_most", (None, 500)),
    ("less_than", (None, 499)),
    ("about", (400, 600)),        # 20% up and down
    ("any", (None, None)),
])
def test_citation_range(op, expected):
    assert Constraints(topic="x", citation_op=op, citations=500).citation_range() == expected


def test_allows_checks_both_limits():
    c = Constraints(topic="x", year_op="after", year=2022, citation_op="at_least", citations=100)
    assert c.allows(paper(2023, 100))
    assert not c.allows(paper(2022, 500))
    assert not c.allows(paper(2024, 99))


def test_missing_data_is_rejected_when_there_is_a_limit():
    c = Constraints(topic="x", year_op="in", year=2020, citation_op="at_least", citations=10)
    assert not c.allows(paper(None, 50))
    assert not c.allows(paper(2020, None))


def test_no_limits_allows_everything():
    assert Constraints(topic="x").allows(paper(None, None))

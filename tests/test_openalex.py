"""Tests for the OpenAlex tool. The internet is replaced by a fake, so no key is needed."""

import httpx

from scout import openalex
from scout.models import Constraints


def work(id_, year, citations, title="A paper"):
    """A fake record shaped like the OpenAlex API answer."""
    return {
        "id": f"https://openalex.org/{id_}",
        "doi": f"https://doi.org/10.1234/{id_}",
        "display_name": title,
        "publication_year": year,
        "cited_by_count": citations,
        "authorships": [{"author": {"display_name": "Ada Lovelace"}}, {"author": {"display_name": "Alan Turing"}}],
        "primary_location": {"landing_page_url": "https://example.org/paper"},
        "abstract_inverted_index": {"agents": [1], "LLM": [0], "tools.": [3], "use": [2]},
    }


def fake_get(works, calls, status=200):
    def get(url, params=None, timeout=None):
        calls.append({"url": url, "params": params})
        return httpx.Response(status, json={"results": works}, request=httpx.Request("GET", url))
    return get


def test_rebuild_abstract_puts_words_in_order():
    assert openalex.rebuild_abstract({"world": [1], "hello": [0, 2]}) == "hello world hello"
    assert openalex.rebuild_abstract(None) is None


def test_to_paper_copies_the_facts():
    p = openalex.to_paper(work("W42", 2023, 150, title="LLM agents"))
    assert (p.paper_id, p.title, p.year, p.citation_count) == ("W42", "LLM agents", 2023, 150)
    assert p.authors == ["Ada Lovelace", "Alan Turing"]
    assert p.url == "https://doi.org/10.1234/W42"
    assert p.abstract == "LLM agents use tools."
    assert "OpenAlex" in p.citation_source and "W42" in p.citation_source


def test_build_filter():
    c = Constraints(topic="x", year_op="after", year=2022, citation_op="about", citations=1000)
    assert openalex.build_filter(c) == (
        "from_publication_date:2023-01-01,cited_by_count:>799,cited_by_count:<1201"
    )
    assert openalex.build_filter(Constraints(topic="x")) == ""


def test_search_removes_papers_that_break_the_limits(monkeypatch):
    works = [work("W1", 2023, 150), work("W2", 2021, 900), work("W3", 2024, 20)]
    calls = []
    monkeypatch.setattr(httpx, "get", fake_get(works, calls))
    c = Constraints(topic="x", year_op="after", year=2022, citation_op="at_least", citations=100)

    found = openalex.search_openalex("llm agents", c)

    assert [p.paper_id for p in found] == ["W1"]
    assert calls[0]["params"]["search"] == "llm agents"
    assert "cited_by_count:>99" in calls[0]["params"]["filter"]


def test_search_falls_back_to_plain_search_when_filter_is_refused(monkeypatch):
    calls = []

    def get(url, params=None, timeout=None):
        calls.append(params)
        status = 400 if "filter" in params else 200
        return httpx.Response(status, json={"results": [work("W1", 2023, 150)]}, request=httpx.Request("GET", url))

    monkeypatch.setattr(httpx, "get", get)
    c = Constraints(topic="x", citation_op="at_least", citations=100)
    assert [p.paper_id for p in openalex.search_openalex("x", c)] == ["W1"]
    assert len(calls) == 2 and "filter" not in calls[1]

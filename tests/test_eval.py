"""Tests for the evaluation graders (no LLM, no internet)."""

from evaluation import run_eval
from scout import openalex
from scout.models import Constraints, Paper, ScoutAnswer

PAPER = Paper(paper_id="W1", title="A", authors=["Ada"], year=2023, citation_count=150,
              citation_source="OpenAlex 'cited_by_count' (https://openalex.org/W1)", url="https://doi.org/10.1/a")
CASE = {"expect_found": True, "year_min": 2023, "year_max": None, "citations_min": 100, "citations_max": None}


def answer(paper):
    return ScoutAnswer(found=paper is not None, paper=paper, explanation="e", uncertainty=[],
                       constraints=Constraints(topic="x"), searches=["x"], llm_requests=3, total_tokens=100)


def test_good_answer_passes_every_check(monkeypatch):
    monkeypatch.setattr(openalex, "get_paper", lambda paper_id: PAPER)
    assert all(run_eval.grade(CASE, answer(PAPER)).values())


def test_wrong_year_and_changed_facts_are_caught(monkeypatch):
    monkeypatch.setattr(openalex, "get_paper", lambda paper_id: PAPER)
    wrong = PAPER.model_copy(update={"year": 2020, "citation_count": 9999})
    checks = run_eval.grade(CASE, answer(wrong))
    assert checks["year_ok"] is False
    assert checks["facts_match_api"] is False


def test_paper_that_does_not_exist_fails_the_source_check(monkeypatch):
    monkeypatch.setattr(openalex, "get_paper", lambda paper_id: None)
    checks = run_eval.grade(CASE, answer(PAPER))
    assert checks["valid_source"] is False and checks["facts_match_api"] is False


def test_saying_no_paper_is_correct_when_none_exists():
    case = {**CASE, "expect_found": False}
    checks = run_eval.grade(case, answer(None))
    assert checks["found_as_expected"] is True
    assert checks["year_ok"] is None  # nothing to check without a paper


def test_report_is_built():
    row = {"id": "T01", "category": "c", "prompt": "p", "error": None, "seconds": 1.0,
           "answer": answer(PAPER).model_dump(), "checks": dict.fromkeys(run_eval.CODE_CHECKS, True)}
    crashed = {"id": "T02", "category": "c", "prompt": "p", "error": "Boom", "seconds": 1.0, "answer": None,
               "checks": {**dict.fromkeys(run_eval.CODE_CHECKS), "found_as_expected": False}}
    report = run_eval.build_report([row, crashed], "test-model")
    assert "| T01 |" in report and "Boom" in report

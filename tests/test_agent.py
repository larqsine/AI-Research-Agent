"""Tests for the whole workflow with a FAKE LLM and a FAKE search (no key, no internet).

The fake LLM lets us test the important promise of this project:
even when the LLM misbehaves, wrong facts cannot reach the final answer.
"""

import pytest
from pydantic_ai import UnexpectedModelBehavior
from pydantic_ai.messages import ModelResponse, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from scout import config, openalex
from scout.agent import run_scout
from scout.models import Paper

REAL = Paper(paper_id="W100", title="Real Paper About LLM Agents", authors=["Ada Lovelace"], year=2023,
             citation_count=250, citation_source="OpenAlex (test)", url="https://doi.org/10.1/real",
             abstract="We study LLM agents.")

CONSTRAINTS = {"topic": "llm agents", "year_op": "after", "year": 2022,
               "citation_op": "at_least", "citations": 100}


def fake_llm(final_choices, search_first=True):
    """Build a fake model. `final_choices` are the answers it gives, one per attempt."""
    choices = list(final_choices)

    def respond(messages, info: AgentInfo) -> ModelResponse:
        output_tool = info.output_tools[0].name
        if not info.function_tools:  # step 1: the parse agent
            return ModelResponse(parts=[ToolCallPart(output_tool, CONSTRAINTS)])
        searched = any(isinstance(part, ToolReturnPart) and part.tool_name == "search_papers"
                       for message in messages for part in message.parts)
        if search_first and not searched:
            return ModelResponse(parts=[ToolCallPart("search_papers", {"query": "llm agents"})])
        return ModelResponse(parts=[ToolCallPart(output_tool, choices.pop(0))])

    return FunctionModel(respond)


def use_fake_search(monkeypatch, papers):
    monkeypatch.setattr(openalex, "search_openalex", lambda query, constraints: papers)


def test_facts_come_from_the_tool_not_from_the_llm(monkeypatch):
    use_fake_search(monkeypatch, [REAL])
    choice = {"paper_id": "W100", "explanation": "It is about LLM agents.", "uncertainty": "None"}

    answer = run_scout("find a paper", model=fake_llm([choice]))

    assert answer.found
    assert answer.paper == REAL
    assert answer.constraints.year_range() == (2023, None)
    assert answer.searches == ["llm agents"]


def test_invented_paper_is_rejected(monkeypatch):
    use_fake_search(monkeypatch, [REAL])
    invented = {"paper_id": "W999", "explanation": "Trust me.", "uncertainty": "None"}
    give_up = {"paper_id": None, "explanation": "Nothing fits.", "uncertainty": "None"}

    answer = run_scout("find a paper", model=fake_llm([invented, give_up]))

    assert not answer.found and answer.paper is None


def test_llm_must_search_before_answering(monkeypatch):
    use_fake_search(monkeypatch, [REAL])
    from_memory = {"paper_id": "W100", "explanation": "I just know it.", "uncertainty": "None"}

    # The fake LLM never calls the tool, so every attempt is refused and the run stops with an error.
    with pytest.raises(UnexpectedModelBehavior):
        run_scout("find a paper", model=fake_llm([from_memory] * 10, search_first=False))


def test_no_paper_found_is_a_valid_answer(monkeypatch):
    use_fake_search(monkeypatch, [])
    nothing = {"paper_id": "null", "explanation": "No paper passed the limits.", "uncertainty": "None"}

    answer = run_scout("find a paper", model=fake_llm([nothing]))

    assert not answer.found
    assert "0 paper(s) passed" in answer.uncertainty[-1]


def test_search_limit_stops_extra_searches(monkeypatch):
    # The fake search remembers every query that really reached OpenAlex.
    real_searches = []
    monkeypatch.setattr(openalex, "search_openalex",
                        lambda query, constraints: real_searches.append(query) or [])
    give_up = {"paper_id": None, "explanation": "Nothing fits.", "uncertainty": "None"}
    wanted = config.MAX_SEARCHES + 2  # the greedy LLM tries 2 searches too many

    def greedy_llm(messages, info: AgentInfo) -> ModelResponse:
        output_tool = info.output_tools[0].name
        if not info.function_tools:  # step 1: the parse agent
            return ModelResponse(parts=[ToolCallPart(output_tool, CONSTRAINTS)])
        tried = sum(isinstance(part, ToolReturnPart) and part.tool_name == "search_papers"
                    for message in messages for part in message.parts)
        if tried < wanted:
            return ModelResponse(parts=[ToolCallPart("search_papers", {"query": f"try {tried + 1}"})])
        return ModelResponse(parts=[ToolCallPart(output_tool, give_up)])

    answer = run_scout("find a paper", model=FunctionModel(greedy_llm))

    # Only the first MAX_SEARCHES calls reach OpenAlex; the extra ones get "Search limit reached".
    assert len(real_searches) == config.MAX_SEARCHES == 4
    assert answer.searches == ["try 1", "try 2", "try 3", "try 4"]
    assert not answer.found


def test_wrong_tool_name_is_retried_and_logged(monkeypatch, caplog):
    # What crashed T02: gpt-oss sometimes answers with a tool called "commentary", which does not exist.
    use_fake_search(monkeypatch, [REAL])
    choice = {"paper_id": "W100", "explanation": "It is about LLM agents.", "uncertainty": "None"}
    wrong_name_used = []

    def confused_llm(messages, info: AgentInfo) -> ModelResponse:
        output_tool = info.output_tools[0].name
        if not info.function_tools:  # step 1: the parse agent
            return ModelResponse(parts=[ToolCallPart(output_tool, CONSTRAINTS)])
        searched = any(isinstance(part, ToolReturnPart) and part.tool_name == "search_papers"
                       for message in messages for part in message.parts)
        if not searched:
            return ModelResponse(parts=[ToolCallPart("search_papers", {"query": "llm agents"})])
        if not wrong_name_used:  # the first answer uses the wrong tool name
            wrong_name_used.append(True)
            return ModelResponse(parts=[ToolCallPart("commentary", choice)])
        return ModelResponse(parts=[ToolCallPart(output_tool, choice)])

    caplog.set_level("INFO", logger="scout")
    answer = run_scout("find a paper", model=FunctionModel(confused_llm))

    assert answer.found and answer.paper == REAL
    assert "LLM called commentary" in caplog.text


def test_step2_starts_again_after_too_many_wrong_tool_names(monkeypatch, caplog):
    # What crashed T10/T13: the LLM kept using tools that do not exist ("json"), 4 times in a row.
    use_fake_search(monkeypatch, [REAL])
    choice = {"paper_id": "W100", "explanation": "It is about LLM agents.", "uncertainty": "None"}
    bad_answers = []

    def stubborn_llm(messages, info: AgentInfo) -> ModelResponse:
        output_tool = info.output_tools[0].name
        if not info.function_tools:  # step 1: the parse agent
            return ModelResponse(parts=[ToolCallPart(output_tool, CONSTRAINTS)])
        searched = any(isinstance(part, ToolReturnPart) and part.tool_name == "search_papers"
                       for message in messages for part in message.parts)
        if not searched:
            return ModelResponse(parts=[ToolCallPart("search_papers", {"query": "llm agents"})])
        if len(bad_answers) < 4:  # 1 answer + 3 retries: enough to make the first attempt fail
            bad_answers.append(True)
            return ModelResponse(parts=[ToolCallPart("json", choice)])
        return ModelResponse(parts=[ToolCallPart(output_tool, choice)])

    caplog.set_level("INFO", logger="scout")
    answer = run_scout("find a paper", model=FunctionModel(stubborn_llm))

    assert answer.found and answer.paper == REAL
    assert "Starting step 2 again" in caplog.text
    assert answer.searches == ["llm agents"]  # the second attempt starts with a clean search list

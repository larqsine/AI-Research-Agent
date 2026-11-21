"""The Research Scout workflow.

    STEP 1  LLM   understand the request        -> Constraints
    STEP 2  LLM   search with the tool, choose  -> Choice (only a paper ID + text)
            CODE  the tool filters by year and citations
    STEP 3  CODE  build the final answer from the tool's data

The LLM never types a title, author, year or citation count into the answer.
Those facts are copied by code from what OpenAlex returned.
"""

import datetime as dt
import logging
from dataclasses import dataclass, field

from pydantic_ai import Agent, ModelRetry, RunContext, UnexpectedModelBehavior, capture_run_messages
from pydantic_ai.messages import RetryPromptPart, ToolCallPart, ToolReturnPart
from pydantic_ai.usage import UsageLimits

from . import config, openalex
from .models import Choice, Constraints, Paper, ScoutAnswer

# Turn this on to see every tool call and every "try again" the LLM got
# (run_eval.py does this with --verbose).
log = logging.getLogger("scout")

STEP2_ATTEMPTS = 2  # how many times step 2 may start from scratch after the LLM breaks the answer format

# ---------------------------------------------------------------- STEP 1 (LLM)

parse_agent = Agent(output_type=Constraints, retries=2, model_settings={"temperature": 0})


@parse_agent.instructions
def parse_instructions() -> str:
    this_year = dt.date.today().year
    return f"""You turn a request for a research paper into search constraints. Today is {dt.date.today()}.

Rules:
- topic: 2-5 keywords for the subject only.
- Year words: "after 2022" -> year_op=after, year=2022. "since/from 2022" -> from.
  "before 2021" -> before. "until/up to 2021" -> until. "in 2020" -> in.
  "between 2019 and 2021" / "from 2019 to 2021" / "2019-2021" -> year_op=between, year=2019, year_end=2021.
  Copy the year exactly as written. Never add or subtract anything yourself.
- Citation words: "at least 100" / "100 or more" -> at_least. "more than / over 500" -> more_than.
  "at most / no more than" -> at_most. "fewer than / less than" -> less_than.
  "about / around / roughly" -> about. Copy the number exactly as written.
- Vague words: "recent", "new", "latest" with no year -> year_op=from, year={this_year - 2}.
  "highly cited", "popular", "influential" with no number -> citation_op=at_least, citations=100.
  Write one sentence in assumptions for each guess like this.
- If the topic can mean different things, pick the meaning that fits a software company
  and say so in assumptions.
- If the request gives no year or no citation limit, leave that part as "any"."""


# ------------------------------------------------------- STEP 2 (LLM + tool)


@dataclass
class SearchState:
    """Memory for one question. The LLM cannot change it; only our code does."""

    constraints: Constraints
    candidates: dict[str, Paper] = field(default_factory=dict)  # every paper that passed the filter
    searches: list[str] = field(default_factory=list)


RESEARCH_INSTRUCTIONS = f"""You are a research scout. Find ONE research paper that fits the user's request.

How to work:
1. Always call search_papers first. You may not answer from memory.
2. The tool already removes papers that break the year or citation limits.
   Your job is to judge if a paper is really about the requested TOPIC.
3. If the results are off-topic or empty, search again with other words
   (a synonym, a broader or a narrower phrase). You have {config.MAX_SEARCHES} searches.
4. Pick the single best paper and copy its paper_id exactly.
   If no paper truly fits the topic, set paper_id to null. Never pick a paper just to have an answer.

Writing rules:
- explanation: give what the user asked for (why it is relevant, a summary, ...) and follow any
  length they asked for. Use ONLY the title and abstract returned by the tool.
- Do not write citation counts, years or author names. The program adds those facts itself.
- uncertainty: say what the user should double-check (missing abstract, weak topic match, ...) or "None".

How to answer:
- Give your final answer ONLY by calling the final_result tool.
- The only tools that exist are search_papers and final_result. There is no "commentary" tool."""

research_agent = Agent(
    deps_type=SearchState,
    output_type=Choice,
    instructions=RESEARCH_INSTRUCTIONS,
    retries=3,
    model_settings={"temperature": 0},
)


@research_agent.tool
def search_papers(ctx: RunContext[SearchState], query: str) -> dict:
    """Search the OpenAlex database for research papers about a topic.

    The user's year and citation limits are applied automatically,
    so every paper in the result is allowed.

    Args:
        query: 2-4 keywords about the topic, for example "retrieval augmented generation".
            Every word must appear in the paper, so fewer words find more papers.
    """
    state = ctx.deps
    if len(state.searches) >= config.MAX_SEARCHES:
        return {"note": "Search limit reached. Choose from the earlier results or set paper_id to null."}

    state.searches.append(query)
    papers = openalex.search_openalex(query, state.constraints)  # deterministic code
    for paper in papers:
        state.candidates[paper.paper_id] = paper

    if not papers:
        return {"results": [], "note": "No paper passed the limits for these words. Try other words."}
    return {"results": [_preview(paper) for paper in papers]}


def _preview(paper: Paper) -> dict:
    """The short version of a paper that the LLM gets to read."""
    abstract = paper.abstract or "(no abstract available)"
    return {
        "paper_id": paper.paper_id,
        "title": paper.title,
        "year": paper.year,
        "citations": paper.citation_count,
        "authors": ", ".join(paper.authors[:3]) + (" et al." if len(paper.authors) > 3 else ""),
        "abstract": abstract[: config.ABSTRACT_PREVIEW],
    }


@research_agent.output_validator
def check_choice(ctx: RunContext[SearchState], choice: Choice) -> Choice:
    """Deterministic guard: the LLM may only choose a paper that the tool really returned."""
    state = ctx.deps
    if not state.searches:
        raise ModelRetry("You must call search_papers before you answer.")

    choice.paper_id = _clean_id(choice.paper_id)
    if choice.paper_id and choice.paper_id not in state.candidates:
        raise ModelRetry(
            f"paper_id {choice.paper_id!r} is not in the search results. "
            "Copy a paper_id exactly from the results, or use null if no paper fits."
        )
    return choice


def _clean_id(paper_id: str | None) -> str | None:
    """'https://openalex.org/w123 ' -> 'W123'. Words like 'null' -> None."""
    if not paper_id or paper_id.strip().lower() in ("null", "none", "n/a"):
        return None
    return paper_id.strip().rstrip("/").rsplit("/", 1)[-1].upper()


def _log_steps(messages) -> None:
    """Write down what the LLM did in step 2: each tool call and each time it was told to retry."""
    for message in messages:
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                log.info("LLM called %s %s", part.tool_name, str(part.args)[:150])
            elif isinstance(part, RetryPromptPart):
                log.info("LLM was told to retry: %s", str(part.content)[:200])
            elif isinstance(part, ToolReturnPart) and str(part.content).startswith("Unknown tool"):
                log.info("LLM used a tool that does not exist: %s", part.content)


def run_scout(question: str, model=None) -> ScoutAnswer:
    """Answer one research request. `model` can be overridden (the tests use a fake model)."""
    model = model or config.MODEL

    # STEP 1 (LLM): understand the request.
    parsed = parse_agent.run_sync(question, model=model)
    constraints = parsed.output

    # STEP 2 (LLM + tool): search and choose. The tool does the filtering in code.
    prompt = (
        f"User request: {question}\n\n"
        f"Limits the search tool enforces for you: {constraints.describe()}\n"
        f"Suggested first search: {constraints.topic}"
    )
    # The LLM sometimes answers with a tool that does not exist ("commentary", "json", ...).
    # After 3 bad answers PydanticAI gives up. Then we start step 2 once more from scratch.
    for attempt in range(1, STEP2_ATTEMPTS + 1):
        state = SearchState(constraints=constraints)  # a fresh start: no old searches or papers
        with capture_run_messages() as messages:
            try:
                # request_limit stops a confused LLM from looping forever (and eating the free quota).
                researched = research_agent.run_sync(
                    prompt, model=model, deps=state, usage_limits=UsageLimits(request_limit=10)
                )
                break
            except UnexpectedModelBehavior as error:
                if attempt == STEP2_ATTEMPTS:
                    raise
                log.info("Step 2 failed (%s). Starting step 2 again.", error)
            finally:  # also on a crash, so we can see what went wrong
                _log_steps(messages)
    choice = researched.output

    # STEP 3 (code): build the answer. Facts come from the tool's data, not from the LLM.
    paper = state.candidates.get(choice.paper_id) if choice.paper_id else None
    if paper and not constraints.allows(paper):  # final safety check, should never trigger
        paper = None

    notes = list(constraints.assumptions)
    if choice.uncertainty.strip().lower() not in ("", "none", "none."):
        notes.append(choice.uncertainty.strip())
    if paper:
        notes.append("Citation counts differ between databases. This one is from OpenAlex.")
        if not paper.abstract:
            notes.append("OpenAlex has no abstract for this paper, so the explanation rests on the title only.")
    else:
        notes.append(
            f"{len(state.searches)} search(es) were tried; "
            f"{len(state.candidates)} paper(s) passed the year and citation limits."
        )

    return ScoutAnswer(
        found=paper is not None,
        paper=paper,
        explanation=choice.explanation,
        uncertainty=notes,
        constraints=constraints,
        searches=state.searches,
        llm_requests=parsed.usage.requests + researched.usage.requests,
        total_tokens=parsed.usage.total_tokens + researched.usage.total_tokens,
    )

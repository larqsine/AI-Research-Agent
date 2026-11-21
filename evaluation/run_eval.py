"""Run the evaluation set and grade every answer.

    python -m evaluation.run_eval                  run all prompts
    python -m evaluation.run_eval --only T01 T09   run only some prompts
    python -m evaluation.run_eval --pause 60       wait 60 s between prompts (for small free tiers)
    python -m evaluation.run_eval --verbose        also print every tool call and retry of the LLM

Writes evaluation/results.md (the report) and evaluation/results.json (raw data).

Two kinds of graders are used:
  * code graders  - objective checks done by this script (year, citations, source, facts)
  * human graders - you read the answer and fill in the "?" cells in results.md
"""

import argparse
import datetime as dt
import json
import logging
import shutil
import time
from pathlib import Path

from pydantic_ai import ModelRateLimitError

from scout import config, openalex
from scout.agent import run_scout
from scout.models import Constraints, ScoutAnswer, in_range

HERE = Path(__file__).parent
YES, NO, NA, HUMAN = "✅", "❌", "—", "?"

CODE_CHECKS = {
    "found_as_expected": "Found a paper when one exists / said so when none exists",
    "year_ok": "Respected the year limit",
    "citations_ok": "Respected the citation limit",
    "valid_source": "Gave a valid source",
    "facts_match_api": "Facts match OpenAlex (nothing made up)",
}


def ask(prompt: str) -> ScoutAnswer:
    """Run the agent. If the free tier says 'too many requests', wait a minute and try again."""
    for attempt in range(3):
        try:
            return run_scout(prompt)
        except ModelRateLimitError:
            if attempt == 2:
                raise
            print("   rate limit reached, waiting 60 s ...")
            time.sleep(60)


def grade(case: dict, answer: ScoutAnswer) -> dict:
    """Code graders. True = pass, False = fail, None = does not apply to this prompt.

    The expected limits come from test_prompts.json (written by hand), NOT from the
    agent's own reading of the prompt. So a misread request is caught here too.
    """
    checks = dict.fromkeys(CODE_CHECKS)
    if case["expect_found"] is not None:
        checks["found_as_expected"] = answer.found == case["expect_found"]

    paper = answer.paper
    if paper is None:
        return checks

    year_limit = (case["year_min"], case["year_max"])
    cite_limit = (case["citations_min"], case["citations_max"])
    if year_limit != (None, None):
        checks["year_ok"] = in_range(paper.year, *year_limit)
    if cite_limit != (None, None):
        checks["citations_ok"] = in_range(paper.citation_count, *cite_limit)

    try:
        fresh = openalex.get_paper(paper.paper_id)
    except openalex.OpenAlexError:
        return checks  # cannot double-check right now, leave the last two checks open
    checks["valid_source"] = bool(
        fresh and (paper.url or "").startswith("http") and "openalex.org" in paper.citation_source
    )
    checks["facts_match_api"] = bool(
        fresh
        and fresh.title == paper.title
        and fresh.year == paper.year
        and fresh.authors[:20] == paper.authors[:20]  # search answers may cut very long author lists
        and _close(fresh.citation_count, paper.citation_count)
    )
    return checks


def _close(a: int | None, b: int | None) -> bool:
    """Citation counts can grow by a few between two lookups, so allow a tiny difference."""
    if a is None or b is None:
        return a == b
    return abs(a - b) <= max(2, 0.01 * b)


def run_case(case: dict) -> dict:
    row = {"id": case["id"], "category": case["category"], "prompt": case["prompt"],
           "error": None, "answer": None, "checks": dict.fromkeys(CODE_CHECKS)}
    start = time.time()
    try:
        answer = ask(case["prompt"])
        row["answer"] = answer.model_dump()
        row["checks"] = grade(case, answer)
    except Exception as error:  # a crash counts as a failed prompt, the run goes on
        row["error"] = f"{type(error).__name__}: {error}"[:300]
        row["checks"]["found_as_expected"] = False
    row["seconds"] = round(time.time() - start, 1)
    return row


def mark(value: bool | None) -> str:
    return {True: YES, False: NO, None: NA}[value]


def build_report(rows: list[dict], model: str) -> str:
    done = [row for row in rows if row["answer"]]
    lines = [
        "# Evaluation results",
        "",
        f"Run on {dt.datetime.now():%Y-%m-%d %H:%M} | model: `{model}` | {len(rows)} prompts | "
        f"{len(rows) - len(done)} crashed",
        "",
        "## Summary (code graders)",
        "",
        "| Check | Passed | Out of |",
        "|---|---|---|",
    ]
    for key, label in CODE_CHECKS.items():
        values = [row["checks"][key] for row in rows if row["checks"][key] is not None]
        lines.append(f"| {label} | {sum(values)} | {len(values)} |")
    if done:
        average = lambda numbers: round(sum(numbers) / len(done), 1)  # noqa: E731
        lines += [
            "",
            f"Per prompt on average: {average([len(r['answer']['searches']) for r in done])} tool calls, "
            f"{average([r['answer']['llm_requests'] for r in done])} LLM requests, "
            f"{average([r['answer']['total_tokens'] for r in done])} tokens, "
            f"{average([r['seconds'] for r in done])} seconds.",
        ]

    lines += [
        "",
        "## Per prompt",
        "",
        f"{YES} pass, {NO} fail, {NA} does not apply, {HUMAN} = a human must fill this in "
        "(read the details below, then replace the ? with ✅ or ❌).",
        "",
        "| ID | What it tests | Found as expected | Year | Citations | Valid source | Facts match API "
        "| Tool calls | Relevant paper (human) | No made-up claims in text (human) | Useful explanation (human) |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        c, answer = row["checks"], row["answer"]
        calls = len(answer["searches"]) if answer else "crash"
        relevant = HUMAN if answer and answer["paper"] else NA
        text = HUMAN if answer else NA
        lines.append(
            f"| {row['id']} | {row['category']} | {mark(c['found_as_expected'])} | {mark(c['year_ok'])} "
            f"| {mark(c['citations_ok'])} | {mark(c['valid_source'])} | {mark(c['facts_match_api'])} "
            f"| {calls} | {relevant} | {text} | {text} |"
        )

    lines += ["", "## Details", ""]
    for row in rows:
        lines += [f"### {row['id']} - {row['category']}", "", f"**Prompt:** {row['prompt']}", ""]
        answer = row["answer"]
        if not answer:
            lines += [f"**Crashed:** `{row['error']}`", ""]
            continue
        lines.append(f"- **Agent understood:** `{Constraints(**answer['constraints']).describe()}`")
        lines.append(f"- **Searches:** {answer['searches']}")
        paper = answer["paper"]
        if paper:
            lines += [
                f"- **Paper:** [{paper['title']}]({paper['url']}) - {paper['year']}, "
                f"{paper['citation_count']} citations",
                f"- **Citation source:** {paper['citation_source']}",
            ]
        else:
            lines.append("- **Paper:** none returned")
        lines += [
            "",
            f"**Explanation by the agent:** {answer['explanation']}",
            "",
            "**Uncertainty notes:** " + " / ".join(answer["uncertainty"]),
            "",
        ]
        if paper:
            abstract = (paper["abstract"] or "(OpenAlex has no abstract)")[:900]
            lines += [f"**Abstract from OpenAlex (to check the explanation against):** {abstract}", ""]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the Research Scout agent")
    parser.add_argument("--only", nargs="*", help="IDs to run, for example: T01 T09")
    parser.add_argument("--pause", type=float, default=45, help="seconds to wait between prompts")
    parser.add_argument("--verbose", action="store_true", help="print every tool call and retry of the LLM")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(format="   | %(message)s")
        logging.getLogger("scout").setLevel(logging.INFO)

    cases = json.loads((HERE / "test_prompts.json").read_text(encoding="utf-8"))
    if args.only:
        cases = [case for case in cases if case["id"] in args.only]

    print(f"Model: {config.MODEL} | {len(cases)} prompts\n")
    rows = []
    for number, case in enumerate(cases):
        if number:
            time.sleep(args.pause)
        print(f"{case['id']}  {case['prompt'][:70]}...")
        row = run_case(case)
        rows.append(row)
        summary = row["error"] or ", ".join(
            f"{key}={'n/a' if value is None else 'PASS' if value else 'FAIL'}"
            for key, value in row["checks"].items()
        )
        print(f"   {summary}  ({row['seconds']} s)\n")

    report = HERE / "results.md"
    if report.exists():  # keep the last report, so hand-filled cells are not lost by accident
        shutil.copy(report, HERE / "results_previous.md")
    report.write_text(build_report(rows, config.MODEL), encoding="utf-8")
    (HERE / "results.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Report written to {report}")
    print("Next: open it and fill in the '?' cells by hand.")


if __name__ == "__main__":
    main()

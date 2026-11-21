# Research Scout Agent

An AI research assistant built with [PydanticAI](https://ai.pydantic.dev/). You ask for a research
paper in plain English (topic, publication year, citation count). The agent searches the
[OpenAlex](https://openalex.org/) database with its own tool, keeps only papers that meet your
limits, picks the one that fits the topic best and explains why.

```
> Find a paper about retrieval-augmented generation published before 2021 with more than 500 citations.

Title:      Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks
Authors:    Patrick Lewis, Ethan Perez, Aleksandra Piktus, ...
Year:       2020
Citations:  10346
Source:     OpenAlex 'cited_by_count' (https://openalex.org/W3027879771), retrieved 2026-11-21
Link:       https://doi.org/10.48550/arxiv.2005.11401
Why it matches: ...
```

**Main idea:** the LLM only reads and chooses. Every fact in the answer (title, authors, year,
citation count, link) is copied by normal Python code from what the search tool returned, so the
LLM cannot invent them.

## Contents

1. [Model choice](#1-model-choice)
2. [Setup](#2-setup)
3. [How to run](#3-how-to-run)
4. [How it works](#4-how-it-works)
5. [Evaluation](#5-evaluation)
6. [Reflection](#6-reflection)
7. [Project structure](#7-project-structure)
8. [Group members and contributions](#8-group-members-and-contributions)
9. [Video](#9-video)

## 1. Model choice

We use **`openai/gpt-oss-120b` on Groq** (set as `SCOUT_MODEL=groq:openai/gpt-oss-120b`).

- **Free:** Groq has a free tier, no credit card needed.
- **Tool calling:** the model supports tool calling, which PydanticAI needs both for our search
  tool and for the structured output.
- **Fast:** one request usually takes 2-6 seconds in total, so running 14 evaluation prompts is quick.
- **Limits:** on the free tier we hit a limit of **200,000 tokens per day** for this model.
  One prompt uses about 3,400 tokens, so a full evaluation run (14 prompts) fits easily, but a lot of
  debugging in one day does not. Groq's current limits are listed at
  <https://console.groq.com/docs/rate-limits>.
- **Weakness we found:** `gpt-oss` sometimes calls tools that do not exist (`commentary`, `json`)
  instead of the answer tool. We handle this in code (see [section 6](#6-reflection)).

You can switch to any other PydanticAI model by changing `SCOUT_MODEL` in `.env`
(for example `groq:llama-3.3-70b-versatile`).

The paper data comes from **OpenAlex**: free, no scraping, and it returns title, authors, year,
citation count, DOI and abstract. A free API key gives a much larger daily budget.

## 2. Setup

Requirements: **Python 3.10 or newer** and git.

### Get the code and install the dependencies

```bash
git clone https://github.com/larqsine/AI-Research-Agent.git
cd AI-Research-Agent

python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

The dependencies are `pydantic-ai-slim[groq]`, `httpx`, `python-dotenv` and `pytest`.

### Configure the API keys

1. Copy `.env.example` to a new file called `.env` in the project folder.
2. Get a free LLM key at <https://console.groq.com/keys> and paste it after `GROQ_API_KEY=`.
3. Get a free OpenAlex key at <https://openalex.org/settings/api> and paste it after `OPENALEX_API_KEY=`.
   (Without it, OpenAlex only allows a few searches per day.)

```
SCOUT_MODEL=groq:openai/gpt-oss-120b
GROQ_API_KEY=your-groq-key
OPENALEX_API_KEY=your-openalex-key
```

`.env` is listed in `.gitignore`, so the keys are never pushed to GitHub. The code reads them with
`python-dotenv` in `scout/config.py`. If the Groq key is missing, `main.py` prints how to fix it.

## 3. How to run

### Ask the agent

```bash
python main.py "Find a paper about LLM agents for software engineering published after 2022 with at least 100 citations."
python main.py --json "..."      # the structured answer as JSON
python main.py                   # type your request when asked
```

The agent supports:

- **Year:** after, from / since, before, until, in, between ("between 2019 and 2021"),
  and "recent" (meaning from 2 years ago, for example from 2024 in 2026).
- **Citations:** at least, more than, at most, fewer than, about / roughly (±20%),
  and "popular" / "highly cited" (meaning at least 100).

### Run the tests (no keys or internet needed)

```bash
python -m pytest
```

The 33 tests replace the LLM and OpenAlex with fakes. They check the limit maths, the OpenAlex
tool, the safety rules of the workflow (for example "a made-up paper ID is refused") and the
evaluation graders.

### Run the evaluation (needs keys)

```bash
python -m evaluation.run_eval                  # all 14 prompts
python -m evaluation.run_eval --only T01 T09   # some prompts
python -m evaluation.run_eval --verbose        # also print every tool call and retry of the LLM
```

This overwrites `evaluation/results.md` and `evaluation/results.json` (the previous report is kept as
`results_previous.md`). After a run, fill in the `?` cells in `results.md` by hand.

## 4. How it works

| # | Step | Done by |
|---|---|---|
| 1 | Read the request and fill in the constraints (topic, year rule, citation rule) | **LLM** (`parse_agent`) |
| 2 | Turn the rules into numbers ("after 2022" → 2023 or later) | **Code** (`Constraints.year_range()`, `citation_range()`) |
| 3 | Choose search words and call the search tool | **LLM** (`research_agent`) |
| 4 | Search OpenAlex and remove papers that break the limits (checked twice) | **Code** (`search_papers` tool, `openalex.py`) |
| 5 | Decide which paper is about the right topic, or say none fits | **LLM** (returns only a paper ID) |
| 6 | Check the LLM searched first and picked a paper the tool really returned | **Code** (`check_choice()`) |
| 7 | Build the answer: copy all facts from the tool's data, add uncertainty notes | **Code** (`run_scout()`) |

The full description, with a diagram and the list of safety rules, is in
[`docs/workflow.md`](docs/workflow.md).

## 5. Evaluation

### 5.1 How AI agents can be evaluated

- **Anthropic, "Demystifying evals for AI agents"** (Anthropic engineering blog): use **code graders**
  for things that can be checked exactly, **model graders** (an LLM as judge) for fuzzy quality, and
  **human graders** as the most trusted check. A small set of realistic tasks is enough to start, and
  you should also test cases where the agent should *not* act (here: when no paper fits).
- **Yehudai et al. 2025, "Survey on Evaluation of LLM-based Agents"**
  (<https://arxiv.org/abs/2503.16416>): judge an agent on more than its final answer. Also measure
  **tool use**, **reliability** (crashes, loops) and **cost** (LLM calls, tokens, time).

### 5.2 Our method

- **14 test prompts** in [`evaluation/test_prompts.json`](evaluation/test_prompts.json). They include the
  three examples from the assignment, broad topics (T07, T11), narrow topics (T05, T06, T08, T14),
  before / after / since / until / exact year / year range, minimum / maximum / approximate citations,
  cases where no paper exists (T09, T10) and ambiguous requests (T11, T12).
- For each prompt, the **correct** limits are written by hand in the JSON file. The grader uses these,
  not the agent's own reading, so a misread request is caught.
- **Code graders** ([`evaluation/run_eval.py`](evaluation/run_eval.py)): found a paper (or correctly said
  none exists), year limit, citation limit, valid source (the paper exists in a fresh OpenAlex lookup),
  facts match that fresh lookup.
- **Human graders:** a person read every explanation next to the paper's abstract and judged:
  relevant paper, no made-up claims, useful explanation. With 14 prompts a human can read everything,
  so we did not add an LLM judge.
- **Cost and tool use:** tool calls, LLM requests, tokens and seconds per prompt.

### 5.3 Results

Final run, 21 Nov 2026, `groq:openai/gpt-oss-120b`, 14 prompts. Full details for every prompt are in
[`evaluation/results.md`](evaluation/results.md).

| Check | Passed |
|---|---|
| Found a paper / said none exists, as expected | 14 / 14 |
| Respected the year limit | 10 / 10 |
| Respected the citation limit | 9 / 9 |
| Gave a valid source | 12 / 12 |
| Facts match OpenAlex | 12 / 12 |
| Relevant paper (human) | 12 / 12 |
| No made-up claims in the explanation (human) | 12 / 14 |
| Useful explanation (human) | 14 / 14 |

Per prompt on average: **1.2 tool calls, 4.0 LLM requests, about 3,400 tokens, 14.4 seconds**
(the time is high because one prompt waited 60 seconds for Groq's rate limit).

How it improved over three runs:

| Run | Prompts | Found as expected | Crashes | No made-up claims |
|---|---|---|---|---|
| 1 (18 Nov) | 12 | 11 / 12 | 1 (T02) | 9 / 11 |
| 2 (21 Nov, after the first fix) | 14 | 13 / 14 | 1 (T13) | not graded |
| 3 (21 Nov, final) | 14 | 14 / 14 | 0 | 12 / 14 |

**Main findings**

- Every fact controlled by code was correct in every run: no broken limits, no wrong titles, years or
  citation counts.
- The errors were in the LLM's own text. T12 calls a paper an "overview" of agents while it actually
  builds a tool *without* an agent, and T02 adds details that are not in the abstract.
- The crashes came from the LLM calling tools that do not exist. They were fixed in code (step 2
  starts again once), and year ranges were added after T13 showed they were missing.

### 5.4 Limits of this evaluation

- Each prompt ran once per run. The agent is not deterministic, so several runs per prompt would
  give a fairer pass rate.
- "Facts match OpenAlex" compares OpenAlex with OpenAlex: it proves our code copied the facts
  correctly, not that OpenAlex is right. Citation counts differ between databases.
- The human grades were given by one person.

## 6. Reflection

The reflection (what worked, what failed, tool calls, hallucinations, how we prevent wrong answers,
and what we would improve) is in [`docs/reflection.md`](docs/reflection.md).

## 7. Project structure

```
main.py                     command line entry point
scout/
  config.py                 settings, reads the keys from .env
  models.py                 data shapes (Constraints, Paper, Choice, ScoutAnswer) and limit checks
  openalex.py               the custom tool: OpenAlex search and filtering
  agent.py                  the PydanticAI agents and the workflow (run_scout)
evaluation/
  test_prompts.json         the 14 test prompts with the correct limits
  run_eval.py               runs the prompts and grades the answers
  results.md / results.json results of the final run, with human grades
docs/
  workflow.md               the workflow, LLM vs code, safety rules
  reflection.md             the reflection
tests/                      33 tests with a fake LLM and fake search
```

## 8. Group members and contributions

| Member | Tasks | Main files |
|---|---|---|
| Radwan El Chaar | Project setup, data models, OpenAlex search tool (task 02) | `scout/config.py`, `scout/models.py`, `scout/openalex.py`, `tests/test_models.py`, `tests/test_openalex.py` |
| Barnabas Tamas | PydanticAI agent, command line, agent workflow (tasks 01 and 03) | `scout/agent.py`, `main.py`, `docs/workflow.md`, `tests/test_agent.py` |
| Yordan Rusev | Evaluation, crash fix and year ranges, reflection (tasks 04 and 05) | `evaluation/`, `tests/test_eval.py`, `docs/reflection.md`, fixes in `scout/agent.py` and `scout/models.py` |

All contributions can be seen in the GitHub commit history.

## 9. Video

Demo video (max 5 minutes): **TODO: add link**

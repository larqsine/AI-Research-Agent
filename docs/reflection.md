# Reflection

Based on our evaluation runs with Groq `openai/gpt-oss-120b`: a first run on 18 Nov 2026 (12 prompts)
and the final run on 21 Nov 2026 (14 prompts, after our fixes). All numbers come from
[`evaluation/results.md`](../evaluation/results.md) (final run).

## What worked well?

- **The facts were always right.** In the final run: year limit 10/10, citation limit 9/9, valid source
  12/12, and title, year, authors and citations matched a fresh OpenAlex lookup 12/12. The first run
  was just as clean. This is because the LLM never writes these facts; the code copies them from the
  search tool.
- **"No paper" answers worked.** In T09 (LLM coding agents before 2010) and T10 (2025 paper with
  more than 200,000 citations) the agent correctly said that no paper fits, in both runs, instead of
  inventing one.
- **Reading the request worked.** All limits were understood correctly, including the tricky ones:
  "after 2022" means 2023 or later, "more than 500" means 501 or more, "roughly 1000" means 800 to
  1200, and (after our fix) "between 2019 and 2021" means 2019 to 2021.
- **Vague words were handled openly.** "Recent" and "popular" became "from 2024" and "at least 100
  citations", and the agent wrote these guesses in the uncertainty notes.
- **The papers were relevant:** 12/12 in the final run, judged by hand.

## What failed or was unreliable?

- **The LLM invents tool names.** Instead of answering with the `final_result` tool, `gpt-oss`
  sometimes calls tools that do not exist: `commentary` (crashed T02 in the first run) and `json`
  (T10, T12, T13 in later runs). After 3 bad answers PydanticAI gives up, so the whole prompt crashed.
  This happened at random: the same prompt could work one time and crash the next.
  **What we did:**
  1. Added logging (`--verbose`) to see every tool call and retry. This is how we found the cause.
  2. Told the LLM in its instructions that only `final_result` exists. This helped (T02 stopped
     crashing) but did not solve it, because the model then used `json` instead.
  3. Made the code start step 2 again from scratch if it fails this way (`STEP2_ATTEMPTS = 2` in
     `scout/agent.py`). In the final run this saved T10 and T12. Result: 0 crashes, down from 1/12
     in the first run and 1/14 in the second.
  4. Added tests with a fake LLM that makes these mistakes.
- **Year ranges were not supported.** In the second run the agent read "between 2019 and 2021" as
  "2019 or later". We added a `between` option; in the final run T13 was understood as 2019 to 2021.
- **The first good paper, not the best one.** In T08 the agent picked CodeXGLUE, while HumanEval would
  fit "benchmarks for LLM code generation" better. It usually stops after the first search.
- **Search is strict.** OpenAlex wants every search word to appear, so long search phrases find little.
  In T09 the agent even put a year into the search words ("code generation language model 2009").
- **The restart costs time.** The average time went up to 14.4 seconds per prompt, mostly because
  T10 needed a restart and then hit Groq's rate limit (106 seconds for that prompt alone).

## How often did the agent need tool calls?

- On average **1.2 tool calls per prompt** in the final run (1.1 in the first). 12 prompts used one
  search; T09 used 2 and T10 used 3. The "no paper" prompts need more searches, because the agent
  tries other words before giving up, which is what we want.
- Every answer needs at least one search, because the code refuses an answer without one.
- On average **4.0 LLM requests per prompt** (4.9 in the first run), while the minimum is 3 (read the
  request, search, answer). The extra requests are mostly retries after a wrong tool name.
  Note: when step 2 is restarted, the requests and tokens of the failed attempt are not counted,
  so the real cost is a bit higher than these numbers.

## Did the LLM ever hallucinate?

Yes, but only in its own text, never in the facts.

- **The same paper was described wrongly in both runs.** For "Demystifying LLM-Based Software Engineering
  Agents" the explanation called it a survey or "overview" (T01 and T12 in the first run, T12 in the
  final run). The abstract says the authors *build* Agentless, a simple tool **without** an agent,
  and show that it beats agent-based tools. The LLM guessed from the title.
- **T02 (final run):** the summary says RAG was tested on "slot-filling" and works "with fewer
  parameters". Neither is in the abstract. The LLM only sees the first 400 characters of the abstract
  and was asked for 5-7 sentences, so it filled the rest from its own memory.
- **Broken rule:** in T01, T07 and T12 the explanation mentions the citation count, which the
  instructions forbid. The numbers were correct, so this broke a rule but was not a made-up fact.
- In the human grading, 12 of 14 explanations had no made-up claims (9 of 11 in the first run).

## How did we prevent incorrect answers?

- **The LLM cannot write facts.** Its answer (`Choice`) only has a paper ID, an explanation and an
  uncertainty note. Title, authors, year, citations and link are copied by code from OpenAlex.
- **It must search first.** An answer without a search is refused (`check_choice()`).
- **It can only pick a paper the tool returned.** A made-up paper ID is refused.
- **Limits are checked twice in code:** once by OpenAlex, and again by `Constraints.allows()`.
- **The LLM does not do the maths.** It copies "after 2022"; the code works out "2023 or later".
- **"No paper found" is a valid answer**, so the LLM is never forced to pick something.
- **Guesses are shown.** Assumptions about vague words, and a note that citation counts differ
  between databases, are added to every answer.
- **Limits on loops:** at most 4 searches and 10 LLM requests per attempt, and at most 2 attempts.
- **A crash is safe:** if the LLM keeps failing, the agent gives no answer, never a wrong one.

## What would we improve with more time?

- **Run every prompt several times** (for example 5) and report a pass rate, because the agent is
  not deterministic.
- **Fix the explanation errors:** give the LLM the full abstract instead of the first 400 characters,
  and add an LLM judge that checks each sentence of the explanation against the abstract.
- **Pick the best paper, not the first:** search with 2-3 different phrases and compare the results.
- **A second source for citations** (for example Semantic Scholar), to show the user how much the
  count differs between databases.
- **Count all retries and restarts** in the results, so the real cost is visible.
- **Try a model with more reliable tool calling**, or use structured JSON output instead of an
  output tool, so wrong tool names cannot happen at all.

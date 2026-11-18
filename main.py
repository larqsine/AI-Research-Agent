"""Run the Research Scout agent from the terminal.

    python main.py "Find a paper about retrieval-augmented generation published before 2021 with more than 500 citations."
    python main.py --json "..."     (prints the structured answer as JSON)
    python main.py                  (asks you to type a request)
"""

import argparse
import sys

from scout import config
from scout.agent import run_scout


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Scout agent")
    parser.add_argument("request", nargs="*", help="what paper you are looking for")
    parser.add_argument("--json", action="store_true", help="print the structured answer as JSON")
    args = parser.parse_args()

    question = " ".join(args.request) or input("What paper are you looking for?\n> ")
    if not question.strip():
        sys.exit("Please type a request.")
    if not config.OPENALEX_API_KEY:
        print("Note: OPENALEX_API_KEY is not set. OpenAlex only allows a few test searches per day without it.\n")

    print(f"Model: {config.MODEL}\nSearching...\n")
    try:
        answer = run_scout(question)
    except Exception as error:  # missing key, rate limit, no internet, confused LLM, ...
        sys.exit(f"The agent could not finish: {type(error).__name__}: {error}")
    print(answer.model_dump_json(indent=2) if args.json else answer.to_text())


if __name__ == "__main__":
    main()

"""Run the Research Scout agent from the terminal.

    python main.py "Find a paper about retrieval-augmented generation published before 2021 with more than 500 citations."
    python main.py --json "..."     (prints the structured answer as JSON)
    python main.py                  (asks you to type a request)
"""

import argparse
import os
import sys

from scout import config
from scout.agent import run_scout

# Where to get a key for each LLM provider we know about.
KEY_PAGES = {"groq": ("GROQ_API_KEY", "https://console.groq.com/keys")}


def missing_key_message() -> str | None:
    """Return a short how-to-fix text if the LLM key is not set, otherwise None."""
    provider = config.MODEL.split(":", 1)[0]
    if provider not in KEY_PAGES:
        return None  # unknown provider: let PydanticAI report it
    key_name, key_page = KEY_PAGES[provider]
    if os.getenv(key_name, "").strip():
        return None
    return (
        f"{key_name} is missing, so the agent cannot talk to the LLM ({config.MODEL}).\n"
        "How to fix it:\n"
        "  1. Copy .env.example to a new file called .env (in the project folder).\n"
        f"  2. Get a free key at {key_page}\n"
        f"  3. Paste it after {key_name}= in .env and run the command again.\n"
        "Never commit the .env file."
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Scout agent")
    parser.add_argument("request", nargs="*", help="what paper you are looking for")
    parser.add_argument("--json", action="store_true", help="print the structured answer as JSON")
    args = parser.parse_args()

    problem = missing_key_message()
    if problem:
        sys.exit(problem)

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

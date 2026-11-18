"""Settings for the agent. Secrets are read from the .env file, never written in code."""

import os

from dotenv import load_dotenv

load_dotenv()  
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")  # keep the terminal output clean

MODEL = os.getenv("SCOUT_MODEL", "groq:openai/gpt-oss-120b")


OPENALEX_API_KEY = os.getenv("OPENALEX_API_KEY", "").strip()

MAX_SEARCHES = 4       # how many times the agent may call the search tool per question
MAX_RESULTS = 5        # how many papers one search shows to the LLM
ABSTRACT_PREVIEW = 400  # characters of the abstract shown to the LLM

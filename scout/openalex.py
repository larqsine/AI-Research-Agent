"""The custom tool: search research papers through the OpenAlex API.

Everything in this file is plain, deterministic code. No LLM is called here.
API docs: https://help.openalex.org/api/
"""

import datetime as dt

import httpx

from . import config
from .models import Constraints, Paper

API_URL = "https://api.openalex.org/works"
# Only ask for the fields we need
FIELDS = (
    "id,doi,display_name,publication_year,cited_by_count,"
    "authorships,primary_location,abstract_inverted_index"
)


class OpenAlexError(RuntimeError):
    """Something went wrong while talking to OpenAlex."""


def build_filter(constraints: Constraints) -> str:
    """Turn the year and citation limits into an OpenAlex filter string."""
    parts = []
    year_low, year_high = constraints.year_range()
    if year_low is not None:
        parts.append(f"from_publication_date:{year_low}-01-01")
    if year_high is not None:
        parts.append(f"to_publication_date:{year_high}-12-31")
    cite_low, cite_high = constraints.citation_range()
    if cite_low is not None and cite_low > 0:
        parts.append(f"cited_by_count:>{cite_low - 1}")
    if cite_high is not None:
        parts.append(f"cited_by_count:<{cite_high + 1}")
    return ",".join(parts)


def rebuild_abstract(inverted_index: dict | None) -> str | None:
    """OpenAlex stores abstracts as {word: [positions]}. Put the words back in order."""
    if not inverted_index:
        return None
    placed = [(pos, word) for word, positions in inverted_index.items() for pos in positions]
    return " ".join(word for _, word in sorted(placed))


def to_paper(work: dict) -> Paper:
    """Convert one raw OpenAlex record into our Paper model."""
    openalex_url = work.get("id") or ""
    location = work.get("primary_location") or {}
    authors = [
        (entry.get("author") or {}).get("display_name")
        for entry in work.get("authorships") or []
    ]
    return Paper(
        paper_id=openalex_url.rsplit("/", 1)[-1],
        title=work.get("display_name") or work.get("title") or "(no title)",
        authors=[name for name in authors if name],
        year=work.get("publication_year"),
        citation_count=work.get("cited_by_count"),
        citation_source=(
            f"OpenAlex 'cited_by_count' ({openalex_url}), retrieved {dt.date.today().isoformat()}"
        ),
        url=work.get("doi") or location.get("landing_page_url") or openalex_url or None,
        doi=work.get("doi"),
        abstract=rebuild_abstract(work.get("abstract_inverted_index")),
    )


def _get(url: str, params: dict) -> httpx.Response:
    """One HTTP GET to OpenAlex, with errors a human can understand."""
    if config.OPENALEX_API_KEY:
        params = {**params, "api_key": config.OPENALEX_API_KEY}
    try:
        response = httpx.get(url, params=params, timeout=30)
    except httpx.HTTPError as error:
        raise OpenAlexError(f"Could not reach OpenAlex ({type(error).__name__}).") from None
    if response.status_code in (401, 403):
        raise OpenAlexError(
            "OpenAlex rejected the API key. Check OPENALEX_API_KEY in .env "
            "and that you verified the e-mail of your OpenAlex account."
        )
    if response.status_code == 429:
        raise OpenAlexError(
            "OpenAlex free budget or rate limit reached. Put a free key in .env "
            "(OPENALEX_API_KEY, from https://openalex.org/settings/api) or try again later."
        )
    return response


def search_openalex(query: str, constraints: Constraints, limit: int = config.MAX_RESULTS) -> list[Paper]:
    """Search OpenAlex by topic and return only papers that respect the constraints.

    The limits are checked twice:
      1. OpenAlex filters on its side (so we get useful results back).
      2. Our own code checks every paper again (so nothing wrong slips through).
    """
    params = {"search": query, "per_page": 25, "select": FIELDS}
    filter_text = build_filter(constraints)
    if filter_text:
        params["filter"] = filter_text

    response = _get(API_URL, params)
    if response.status_code == 400:
        response = _get(API_URL, {"search": query, "per_page": 25})
    if response.status_code != 200:
        raise OpenAlexError(f"OpenAlex answered with HTTP {response.status_code}: {response.text[:200]}")

    papers = [to_paper(work) for work in response.json().get("results", [])]
    return [paper for paper in papers if constraints.allows(paper)][:limit]


def get_paper(paper_id: str) -> Paper | None:
    """Fetch one paper by its OpenAlex ID. The evaluation uses this to double-check answers."""
    response = _get(f"{API_URL}/{paper_id}", {"select": FIELDS})
    if response.status_code == 404:
        return None
    if response.status_code != 200:
        raise OpenAlexError(f"OpenAlex answered with HTTP {response.status_code}: {response.text[:200]}")
    return to_paper(response.json())

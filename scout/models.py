"""The data shapes used by the agent, plus the constraint checks.

Everything in this file is plain, deterministic code. No LLM is called here.
"""

from typing import Literal

from pydantic import BaseModel, Field

ABOUT_TOLERANCE = 0.20  # "about 1000 citations" means 800 to 1200


class Constraints(BaseModel):
    """What the user asked for. The LLM fills this in (step 1 of the workflow)."""

    topic: str = Field(
        description="The research topic as a short search phrase of 2-5 keywords. No years, no numbers."
    )
    year_op: Literal["any", "after", "from", "before", "until", "in", "between"] = Field(
        "any",
        description=(
            "How the publication year is limited. after = later than the year, "
            "from = that year or later, before = earlier than the year, "
            "until = that year or earlier, in = exactly that year, "
            "between = from year to year_end (both included), any = no limit."
        ),
    )
    year: int | None = Field(
        None, description="The year exactly as the user wrote it. null when year_op is 'any'."
    )
    year_end: int | None = Field(
        None, description="Only for year_op 'between': the second year as the user wrote it. Otherwise null."
    )
    citation_op: Literal["any", "at_least", "more_than", "at_most", "less_than", "about"] = Field(
        "any", description="How the citation count is limited. any = no limit."
    )
    citations: int | None = Field(
        None, description="The number exactly as the user wrote it. null when citation_op is 'any'."
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="One short sentence for every guess you made (vague words, unclear topic). Empty if none.",
    )

    # --- deterministic helpers: the code does the math, not the LLM ---

    def year_range(self) -> tuple[int | None, int | None]:
        """Lowest and highest allowed year (None = no limit on that side)."""
        y = self.year
        if y is None:
            return (None, None)
        if self.year_op == "between":  # "between 2021 and 2019" works too; no second year = "from"
            if self.year_end is None:
                return (y, None)
            return (min(y, self.year_end), max(y, self.year_end))
        return {
            "any": (None, None),
            "after": (y + 1, None),
            "from": (y, None),
            "before": (None, y - 1),
            "until": (None, y),
            "in": (y, y),
        }[self.year_op]

    def citation_range(self) -> tuple[int | None, int | None]:
        """Lowest and highest allowed citation count (None = no limit on that side)."""
        c = self.citations
        if c is None:
            return (None, None)
        return {
            "any": (None, None),
            "at_least": (c, None),
            "more_than": (c + 1, None),
            "at_most": (None, c),
            "less_than": (None, c - 1),
            "about": (round(c * (1 - ABOUT_TOLERANCE)), round(c * (1 + ABOUT_TOLERANCE))),
        }[self.citation_op]

    def allows(self, paper: "Paper") -> bool:
        """True only if the paper respects BOTH the year and the citation limits."""
        return in_range(paper.year, *self.year_range()) and in_range(
            paper.citation_count, *self.citation_range()
        )

    def describe(self) -> str:
        return (
            f"topic: {self.topic!r} | year: {_range_text(*self.year_range())} | "
            f"citations: {_range_text(*self.citation_range())}"
        )


def in_range(value: int | None, low: int | None, high: int | None) -> bool:
    """Is value between low and high? A missing value fails as soon as there is a limit."""
    if low is None and high is None:
        return True
    if value is None:
        return False  # we cannot verify it, so we do not accept it
    return (low is None or value >= low) and (high is None or value <= high)


def _range_text(low: int | None, high: int | None) -> str:
    if low is None and high is None:
        return "any"
    if low == high:
        return f"exactly {low}"
    if high is None:
        return f"{low} or higher"
    if low is None:
        return f"{high} or lower"
    return f"{low} to {high}"


class Paper(BaseModel):
    """One paper, exactly as the search tool got it from OpenAlex."""

    paper_id: str  # OpenAlex ID
    title: str
    authors: list[str]
    year: int | None
    citation_count: int | None
    citation_source: str
    url: str | None
    doi: str | None = None
    abstract: str | None = None


class Choice(BaseModel):
    """What the LLM returns in step 2.

    Notice what is NOT here: title, authors, year, citation count, link.
    The LLM only points at a paper by its ID. The facts are added later by code.
    """

    paper_id: str | None = Field(
        description="The paper_id of the best paper, copied exactly from the search results. null if no paper fits."
    )
    explanation: str = Field(
        description=(
            "What the user asked for (why the paper is relevant, a summary, ...), based only on the "
            "title and abstract from the search tool. If no paper fits, explain why."
        )
    )
    uncertainty: str = Field(
        description="Anything the user should double-check, or 'None'."
    )


class ScoutAnswer(BaseModel):
    """The final structured answer the user gets."""

    found: bool
    paper: Paper | None  # title, authors, year, citation count, source and link live here
    explanation: str
    uncertainty: list[str]
    constraints: Constraints
    searches: list[str]
    llm_requests: int
    total_tokens: int

    def to_text(self) -> str:
        """A readable version for the terminal."""
        lines = [f"Understood as -> {self.constraints.describe()}", ""]
        if self.paper:
            p = self.paper
            authors = ", ".join(p.authors[:8]) + (" et al." if len(p.authors) > 8 else "")
            lines += [
                f"Title:      {p.title}",
                f"Authors:    {authors or '(not listed)'}",
                f"Year:       {p.year}",
                f"Citations:  {p.citation_count}",
                f"Source:     {p.citation_source}",
                f"Link:       {p.url}",
                "",
                "Why it matches:",
            ]
        else:
            lines += ["No paper found that fits the request.", "", "Why:"]
        lines += [self.explanation, "", "Uncertainty / notes:"]
        lines += [f"- {note}" for note in self.uncertainty] or ["- None"]
        lines += [
            "",
            f"(tool calls: {len(self.searches)} {self.searches} | "
            f"LLM requests: {self.llm_requests} | tokens: {self.total_tokens})",
        ]
        return "\n".join(lines)

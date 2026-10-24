"""Structured-output contract for the Gemini receipt candidate.

The model may only produce narrative + insight dicts. Every integer,
mode, date, and goal claim is re-validated deterministically by
`app.agents.fact_guard` before anything is persisted — this schema is the
shape, never the source of truth.
"""

from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CandidateInsight(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=500)
    evidence_event_ids: List[str] = Field(min_length=1)


class RecapCandidate(BaseModel):
    """What Gemini is allowed to propose. Deterministic code decides
    whether any of it is supported by DailyContext."""

    model_config = ConfigDict(extra="forbid")

    narrative: str = Field(min_length=1, max_length=2000)
    insights: List[CandidateInsight] = Field(default_factory=list, max_length=8)
    highlight_media_ids: List[str] = Field(default_factory=list, max_length=6)
    directive_for_next_cycle: Optional[str] = Field(default=None, max_length=300)

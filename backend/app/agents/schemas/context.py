"""Typed provider inputs for the recap chain (HWGA07).

These are internal shapes, not API contracts — the locked client-facing
models live in `app/schemas/contracts.py`. They are the ONLY structured
context the provider may see for weekly recaps and morning directives:

- `WeeklyContext` is built exclusively from stored DAILY recap objects
  (plus active goals). Raw event history never reaches the model.
- `DirectiveContext` is built from the stored recap(s) and goal state.

Both carry the evidence ids every downstream claim must trace to, so the
deterministic guard can verify grounding after the model proposes.
"""

from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel

from app.schemas.contracts import GoalItem


class RecapRef(BaseModel):
    """A stored recap as visible to the model — narrative and grounding
    only. `evidence_event_ids` is the union of ids cited by that recap's
    persisted insights, so weekly insights can trace back to real events."""

    recap_id: UUID
    period_start: date
    narrative: str
    status: str
    insights: List[dict]
    evidence_event_ids: List[UUID]
    highlight_media_ids: List[UUID]
    directive_for_next_cycle: Optional[str] = None


class DirectiveContext(BaseModel):
    """Everything the directive proposal may draw on for `for_date`."""

    user_id: UUID
    for_date: date
    timezone: str
    latest_recap: Optional[RecapRef] = None
    recent_recaps: List[RecapRef] = []  # up to 3, most recent first
    goals: List[GoalItem] = []


class WeeklyContext(BaseModel):
    """Stored DAILY recaps compacted into one week — never raw events."""

    user_id: UUID
    timezone: str
    week_start: date
    week_end: date
    days_covered: int
    missing_dates: List[date] = []
    daily_recaps: List[RecapRef] = []
    evidence_event_ids: List[UUID] = []
    highlight_media_ids: List[UUID] = []
    goals: List[GoalItem] = []

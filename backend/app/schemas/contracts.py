"""Typed models — verbatim from docs/hwga/contracts.md §2 (LOCKED HWGA01).
V2 additions are verbatim from docs/hwga/v2/contracts_v2.md §1 (LOCKED V2A)."""

from datetime import date, datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.enums import (
    ConfirmationKind,
    EventType,
    GenerationStatus,
    GoalStatus,
    MediaKind,
    RecapPeriod,
    TranscriptState,
    UserMode,
)


class ErrorResponse(BaseModel):
    code: str
    message: str
    details: dict = Field(default_factory=dict)


class EventIn(BaseModel):
    type: EventType
    kind: Optional[ConfirmationKind] = None
    mode: Optional[UserMode] = None
    occurred_at: Optional[datetime] = None
    idempotency_key: str


class GoalItem(BaseModel):
    id: UUID
    title: str
    status: GoalStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    age_days: int


class MediaAssetMeta(BaseModel):
    id: UUID
    kind: MediaKind
    captured_at: datetime
    mime_type: str
    byte_length: int
    duration_sec: Optional[float] = None
    transcript_state: TranscriptState
    transcript_text: Optional[str] = None


class ModeInterval(BaseModel):
    mode: UserMode
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_min: Optional[int] = None


class DailyContext(BaseModel):
    """Deterministic aggregator output — the ONLY structured input to Gemini."""

    user_id: UUID
    local_date: date
    timezone: str
    confirmations: dict
    quiet_moments: int
    mode_intervals: List[ModeInterval]
    ideas: List[dict]
    media_asset_ids: List[UUID]
    goals: List[GoalItem]
    evidence_event_ids: List[UUID]


class Recap(BaseModel):
    id: UUID
    user_id: UUID
    period_type: RecapPeriod
    period_start: date
    period_end: date
    narrative: str
    insights: List[dict]
    highlight_media_ids: List[UUID]
    directive_for_next_cycle: Optional[str] = None
    source_recap_ids: List[UUID]
    status: GenerationStatus
    created_at: datetime


class MorningDirective(BaseModel):
    id: UUID
    user_id: UUID
    for_date: date
    content: str
    source_recap_id: Optional[UUID] = None
    status: GenerationStatus
    shown_at: Optional[datetime] = None


# --- V2 additions (contracts_v2.md §1, LOCKED V2A) ---


class WidgetState(BaseModel):
    """One lightweight read model for both home-screen widgets. Everything
    on it is already computable from V1 contracts — this is a convenience
    aggregate, not a new truth."""

    generated_at: datetime
    mode: Optional[ModeInterval] = None
    today_confirmations: dict[ConfirmationKind, int] = Field(default_factory=dict)
    quiet_moments_today: int = 0
    goals_active: int = 0
    oldest_goal_age_days: Optional[int] = None
    directive_line: Optional[str] = None
    directive_status: Optional[GenerationStatus] = None
    receipt_status: Optional[GenerationStatus] = None
    receipt_stale: bool = False

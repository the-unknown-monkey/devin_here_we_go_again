"""Deterministic DailyContext aggregation (contracts.md §2, TRD §4).

Every fact the receipt may state is computed here, in code: local-date
boundaries from `users.timezone`, confirmation counts, quiet-moment count,
mode intervals clipped to the day with derived durations, media references
(authenticated ids only), voice-scrap ideas (transcript text only — never
media bytes), active goals with server-computed `age_days`, and the
evidence event ids every claim must trace to.

Missing = unknown: unlogged confirmation kinds are OMITTED from
`confirmations`; the narrative must never assert something did not happen.
"""

import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.db.models import User
from app.db.repositories.events import EventRepository
from app.db.repositories.goals import GoalRepository
from app.db.repositories.media import MediaAssetRepository
from app.db.repositories.modes import ModeIntervalRepository
from app.domain.enums import ConfirmationKind, EventType, GoalStatus, MediaKind
from app.schemas.contracts import DailyContext, GoalItem, ModeInterval
from app.services.goals import _age_days
from app.services.modes import _aware


@dataclass
class AggregatedDay:
    """DailyContext plus a deterministic evidence index used by the fact
    guard and the fallback receipt (which fact traces to which event ids).
    Never serialized to the client or the provider."""

    context: DailyContext
    evidence_by_fact: dict[str, list[uuid.UUID]] = field(default_factory=dict)


def local_day_window(tz: ZoneInfo, local_date: date) -> tuple[datetime, datetime]:
    """Half-open [start, end) UTC window for a user-local calendar date."""
    start = datetime.combine(local_date, time.min, tzinfo=tz).astimezone(UTC)
    return start, start + timedelta(days=1)


def _clip(value: datetime, low: datetime, high: datetime) -> datetime:
    return max(low, min(value, high))


class DailyContextService:
    def __init__(self, session: Session):
        self.session = session
        self.events = EventRepository(session)
        self.intervals = ModeIntervalRepository(session)
        self.media = MediaAssetRepository(session)
        self.goals = GoalRepository(session)

    def build(self, user: User, local_date: date) -> AggregatedDay:
        tz = ZoneInfo(user.timezone)
        start, end = local_day_window(tz, local_date)
        now = datetime.now(UTC)

        day_events = self.events.list_between(user.id, start, end)
        evidence_by_fact: dict[str, list[uuid.UUID]] = {}

        # Confirmation counts — only logged kinds appear (missing = unknown).
        confirmations: dict[str, int] = {}
        for kind in ConfirmationKind:
            ids = [
                e.id
                for e in day_events
                if e.type == EventType.CONFIRMATION and e.kind == kind
            ]
            if ids:
                confirmations[kind.value] = len(ids)
                evidence_by_fact[f"confirmation:{kind.value}"] = ids

        quiet_ids = [e.id for e in day_events if e.type == EventType.QUIET_MOMENT]
        if quiet_ids:
            evidence_by_fact["quiet_moments"] = quiet_ids

        transition_ids = [
            e.id for e in day_events if e.type == EventType.MODE_TRANSITION
        ]
        if transition_ids:
            evidence_by_fact["mode_transitions"] = transition_ids

        # Mode intervals overlapping the window, clipped to the day so the
        # derived duration_min can never exceed the window's bounds.
        mode_intervals: list[ModeInterval] = []
        for row in self.intervals.list_overlapping(user.id, start, end):
            row_start = _aware(row.started_at)
            row_end = _aware(row.ended_at) if row.ended_at else min(now, end)
            clipped_start = _clip(row_start, start, end)
            clipped_end = _clip(row_end, start, end)
            if clipped_end <= clipped_start:
                continue
            mode_intervals.append(
                ModeInterval(
                    mode=row.mode,
                    started_at=clipped_start,
                    ended_at=clipped_end if row.ended_at else None,
                    duration_min=int((clipped_end - clipped_start).total_seconds() // 60),
                )
            )
            evidence_by_fact.setdefault(f"mode:{row.mode.value}", []).extend(
                transition_ids
            )

        # Media captured that day — ids only; bytes never leave the backend.
        assets = self.media.list_for_user_between(user.id, start, end)
        media_event_ids = [
            e.id for e in day_events if e.type == EventType.MEDIA_CAPTURED
        ]
        if media_event_ids:
            evidence_by_fact["media_captured"] = media_event_ids

        # Voice-scrap ideas: transcript text only (MANUAL_TEXT / COMPLETED).
        ideas = [
            {
                "media_id": str(a.id),
                "captured_at": _aware(a.captured_at).isoformat(),
                "transcript_text": a.transcript_text,
            }
            for a in assets
            if a.kind == MediaKind.VOICE and a.transcript_text
        ]
        if ideas:
            evidence_by_fact["ideas"] = media_event_ids

        goal_items = [
            GoalItem(
                id=g.id,
                title=g.title,
                status=g.status,
                created_at=_aware(g.created_at),
                resolved_at=_aware(g.resolved_at) if g.resolved_at else None,
                age_days=_age_days(g.created_at, tz, now),
            )
            for g in self.goals.list_for_user(user.id)
            if g.status == GoalStatus.ACTIVE
        ]

        context = DailyContext(
            user_id=user.id,
            local_date=local_date,
            timezone=user.timezone,
            confirmations=confirmations,
            quiet_moments=len(quiet_ids),
            mode_intervals=mode_intervals,
            ideas=ideas,
            media_asset_ids=[a.id for a in assets],
            goals=goal_items,
            evidence_event_ids=[e.id for e in day_events],
        )
        return AggregatedDay(context=context, evidence_by_fact=evidence_by_fact)

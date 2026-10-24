"""Deterministic WeeklyContext builder (HWGA07).

The weekly recap consumes stored DAILY recap objects only — never raw
events. This builder owns the ISO week window (Monday start, user-local),
period completeness (which expected days have no stored receipt), the
evidence-id union carried forward from the daily insights, and the media
reference union. Everything the model may claim is computed here.
"""

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.agents.schemas.context import RecapRef, WeeklyContext
from app.db.models import RecapRow, User
from app.db.repositories.goals import GoalRepository
from app.db.repositories.recaps import RecapRepository
from app.domain.enums import GoalStatus
from app.schemas.contracts import GoalItem
from app.services.goals import _age_days
from app.services.modes import _aware


def week_bounds(local_date: date) -> tuple[date, date]:
    """ISO week window [Monday, Sunday] containing `local_date`."""
    start = local_date - timedelta(days=local_date.weekday())
    return start, start + timedelta(days=6)


def _evidence_union(row: RecapRow) -> list[uuid.UUID]:
    ids: list[uuid.UUID] = []
    for ins in row.insights or []:
        for raw in ins.get("evidence_event_ids", []):
            try:
                ids.append(uuid.UUID(str(raw)))
            except (ValueError, AttributeError, TypeError):
                continue
    return ids


def _media_union(row: RecapRow) -> list[uuid.UUID]:
    out: list[uuid.UUID] = []
    for raw in row.highlight_media_ids or []:
        try:
            out.append(uuid.UUID(str(raw)))
        except (ValueError, AttributeError, TypeError):
            continue
    return out


def recap_ref(row: RecapRow) -> RecapRef:
    """A stored recap as the model may see it — grounding carried, no
    storage keys, no raw events."""
    return RecapRef(
        recap_id=row.id,
        period_start=row.period_start,
        narrative=row.narrative,
        status=row.status.value,
        insights=list(row.insights or []),
        evidence_event_ids=_evidence_union(row),
        highlight_media_ids=_media_union(row),
        directive_for_next_cycle=row.directive_for_next_cycle,
    )


@dataclass
class AggregatedWeek:
    context: WeeklyContext
    source_rows: list[RecapRow]


class WeeklyContextService:
    def __init__(self, session: Session):
        self.session = session
        self.recaps = RecapRepository(session)
        self.goals = GoalRepository(session)

    def build(self, user: User, local_date: date) -> AggregatedWeek:
        tz = ZoneInfo(user.timezone)
        week_start, week_end = week_bounds(local_date)
        today = datetime.now(UTC).astimezone(tz).date()

        # Days expected to have a receipt: week_start..min(week_end, today).
        # Future days are not "missing" — they haven't happened yet.
        last_expected = min(week_end, today)
        expected = {
            week_start + timedelta(days=i)
            for i in range((last_expected - week_start).days + 1)
        } if last_expected >= week_start else set()

        rows = self.recaps.list_daily_between(user.id, week_start, week_end)
        stored_dates = {r.period_start for r in rows}
        missing = sorted(expected - stored_dates)

        evidence: list[uuid.UUID] = []
        media: list[uuid.UUID] = []
        refs: list[RecapRef] = []
        for row in rows:
            ref = recap_ref(row)
            refs.append(ref)
            evidence.extend(ref.evidence_event_ids)
            media.extend(ref.highlight_media_ids)

        now = datetime.now(UTC)
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

        ctx = WeeklyContext(
            user_id=user.id,
            timezone=user.timezone,
            week_start=week_start,
            week_end=week_end,
            days_covered=len(rows),
            missing_dates=missing,
            daily_recaps=refs,
            evidence_event_ids=list(dict.fromkeys(evidence)),
            highlight_media_ids=list(dict.fromkeys(media)),
            goals=goal_items,
        )
        return AggregatedWeek(context=ctx, source_rows=rows)

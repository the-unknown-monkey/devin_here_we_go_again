"""Recap fetch/generation service (contracts.md §3-4).

- GET /recaps returns the stored receipt; if missing or marked stale by a
  backfilled event it is (re)generated idempotently — uniqueness on
  (user_id, period_type, period_start) is enforced by the DB constraint,
  so retries can never create duplicates.
- The LangGraph workflow owns generation; this service owns session,
  period math, provider selection, and contract serialization.
- The Gemini provider is constructed lazily from backend settings only.
  Without a key the run falls back deterministically — never a fake
  "generated" receipt.
"""

import uuid
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.agents.graphs.daily_receipt import build_daily_graph
from app.agents.graphs.weekly_recap import build_weekly_graph
from app.agents.providers.gemini import GeminiProvider, NarrativeProvider
from app.core.config import get_settings
from app.db.models import RecapRow, User
from app.db.repositories.recaps import RecapRepository
from app.domain import errors
from app.domain.enums import GenerationStatus, RecapPeriod
from app.schemas.contracts import Recap
from app.services.modes import _aware


def serialize_recap(row: RecapRow) -> Recap:
    return Recap(
        id=row.id,
        user_id=row.user_id,
        period_type=row.period_type,
        period_start=row.period_start,
        period_end=row.period_end,
        narrative=row.narrative,
        insights=row.insights or [],
        highlight_media_ids=[uuid.UUID(str(i)) for i in (row.highlight_media_ids or [])],
        directive_for_next_cycle=row.directive_for_next_cycle,
        source_recap_ids=[uuid.UUID(str(i)) for i in (row.source_recap_ids or [])],
        status=row.status,
        created_at=_aware(row.created_at),
    )


class RecapService:
    def __init__(self, session: Session, provider: NarrativeProvider | None = None):
        self.session = session
        self.recaps = RecapRepository(session)
        self._provider = provider

    def _get_provider(self) -> NarrativeProvider:
        if self._provider is None:
            self._provider = GeminiProvider(api_key=get_settings().gemini_api_key)
        return self._provider

    def _local_date(self, user: User, value: date | None) -> date:
        if value is not None:
            return value
        return datetime.now(UTC).astimezone(ZoneInfo(user.timezone)).date()

    def get_or_generate(
        self,
        user: User,
        period: RecapPeriod,
        local_date: date | None,
    ) -> Recap:
        if period == RecapPeriod.WEEKLY:
            return self._get_or_generate_weekly(user, local_date)
        if period != RecapPeriod.DAILY:
            # MONTHLY/YEARLY remain contract-level only — post-V1.
            raise errors.not_found(f"{period.value} recaps are not generated yet")

        day = self._local_date(user, local_date)
        existing = self.recaps.get_for_period(user.id, period, day)
        if existing is not None and not existing.stale:
            return serialize_recap(existing)

        graph = build_daily_graph(self.session, self._get_provider())
        result = graph.invoke({"user_id": user.id, "local_date": day})

        row = result.get("recap")
        if row is None or result.get("status") == GenerationStatus.FAILED:
            raise errors.DomainError(
                "GENERATION_FAILED",
                "The receipt could not be saved right now — please try again.",
                500,
            )
        return serialize_recap(row)

    def _weekly_needs_regen(
        self, user: User, week_start: date, week_end: date, row: RecapRow
    ) -> bool:
        """Deterministic staleness: regenerate once if any stored daily
        recap in the window is stale/newer than the weekly, or the set of
        source daily recaps changed since generation."""
        if row.stale:
            return True
        dailies = self.recaps.list_daily_between(user.id, week_start, week_end)
        created = _aware(row.created_at)
        if any(d.stale or _aware(d.created_at) > created for d in dailies):
            return True
        current_ids = {str(d.id) for d in dailies}
        return current_ids != {str(i) for i in (row.source_recap_ids or [])}

    def _get_or_generate_weekly(self, user: User, local_date: date | None) -> Recap:
        from app.services.weekly_context import week_bounds

        day = self._local_date(user, local_date)
        week_start, week_end = week_bounds(day)

        existing = self.recaps.get_for_period(user.id, RecapPeriod.WEEKLY, week_start)
        if existing is not None:
            if not self._weekly_needs_regen(user, week_start, week_end, existing):
                return serialize_recap(existing)
            # Regenerate once under the same period key (D20 semantics):
            # the persist node only overwrites a row flagged stale.
            existing.stale = True
            self.session.flush()

        graph = build_weekly_graph(self.session, self._get_provider())
        result = graph.invoke({"user_id": user.id, "local_date": day})

        row = result.get("recap")
        if row is None or result.get("status") == GenerationStatus.FAILED:
            raise errors.DomainError(
                "GENERATION_FAILED",
                "The weekly recap could not be saved right now — please try again.",
                500,
            )
        return serialize_recap(row)

    def mark_stale_for_local_date(self, user: User, occurred_at: datetime) -> None:
        """Backfill rule (contracts §4): an event landing in an
        already-generated past period marks that recap stale; the next
        fetch regenerates it once."""
        local_day = _aware(occurred_at).astimezone(ZoneInfo(user.timezone)).date()
        row = self.recaps.get_for_period(user.id, RecapPeriod.DAILY, local_day)
        if row is not None and row.status in (
            GenerationStatus.GENERATED,
            GenerationStatus.FALLBACK,
        ) and _aware(occurred_at) < _aware(row.created_at):
            row.stale = True
            self.session.flush()

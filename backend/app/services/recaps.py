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
        if period != RecapPeriod.DAILY:
            # WEEKLY roll-up arrives in HWGA07; MONTHLY/YEARLY are post-V1.
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

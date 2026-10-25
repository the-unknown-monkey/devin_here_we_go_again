"""Morning directive fetch/generation service (HWGA07, contracts §3-4).

- GET /directive/today returns the stored directive, generating it
  idempotently on first open — uniqueness on (user_id, for_date) means
  retries and duplicate opens can never create duplicates.
- `shown_at` marks first display; generation never repeats because a
  card was rendered again.
- The context is deterministic: stored non-stale DAILY recaps plus
  active goals. No recap yet still yields an honest directive — the
  deterministic fallback never pretends to know something.
"""

import uuid
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.agents.providers.gemini import GeminiProvider, NarrativeProvider
from app.agents.schemas.context import DirectiveContext
from app.core.config import get_settings
from app.db.models import MorningDirectiveRow, User
from app.db.repositories.goals import GoalRepository
from app.db.repositories.recaps import DirectiveRepository, RecapRepository
from app.domain import errors
from app.domain.enums import GenerationStatus, GoalStatus
from app.schemas.contracts import GoalItem, MorningDirective
from app.services.goals import _age_days
from app.services.modes import _aware
from app.services.weekly_context import recap_ref


def serialize_directive(row: MorningDirectiveRow) -> MorningDirective:
    return MorningDirective(
        id=row.id,
        user_id=row.user_id,
        for_date=row.for_date,
        content=row.content,
        source_recap_id=row.source_recap_id,
        status=row.status,
        shown_at=_aware(row.shown_at) if row.shown_at else None,
    )


class DirectiveContextBuilder:
    """Deterministic input for the directive workflow: the most recent
    stored recap, up to 3 recent recaps, and active goals with age_days."""

    def __init__(self, session: Session):
        self.session = session
        self.recaps = RecapRepository(session)
        self.goals = GoalRepository(session)

    def build(self, user: User, for_date: date) -> DirectiveContext:
        tz = ZoneInfo(user.timezone)
        now = datetime.now(UTC)
        latest = self.recaps.latest_daily_before(user.id, for_date)
        recent = self.recaps.recent_dailies(user.id, limit=3)
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
        return DirectiveContext(
            user_id=user.id,
            for_date=for_date,
            timezone=user.timezone,
            latest_recap=recap_ref(latest) if latest is not None else None,
            recent_recaps=[recap_ref(r) for r in recent],
            goals=goal_items,
        )


class DirectiveService:
    def __init__(self, session: Session, provider: NarrativeProvider | None = None):
        self.session = session
        self.directives = DirectiveRepository(session)
        self._provider = provider

    def _get_provider(self) -> NarrativeProvider:
        if self._provider is None:
            self._provider = GeminiProvider(
                api_key=get_settings().gemini_api_key,
                model=get_settings().gemini_model,
            )
        return self._provider

    def get_or_generate_today(
        self, user: User, now: datetime | None = None
    ) -> MorningDirective:
        now = now or datetime.now(UTC)
        for_date = _aware(now).astimezone(ZoneInfo(user.timezone)).date()

        existing = self.directives.get_for_date(user.id, for_date)
        if existing is not None:
            self._mark_shown(existing, now)
            return serialize_directive(existing)

        from app.agents.graphs.morning_directive import build_directive_graph

        graph = build_directive_graph(self.session, self._get_provider())
        result = graph.invoke({"user_id": user.id, "for_date": for_date})

        row = result.get("directive")
        if row is None or result.get("status") == GenerationStatus.FAILED:
            raise errors.DomainError(
                "GENERATION_FAILED",
                "The directive could not be saved right now — please try again.",
                500,
            )
        self._mark_shown(row, now)
        return serialize_directive(row)

    def _mark_shown(self, row: MorningDirectiveRow, now: datetime) -> None:
        """First display only — later opens never regenerate or re-stamp."""
        if row.shown_at is None:
            row.shown_at = _aware(now)
            self.session.commit()

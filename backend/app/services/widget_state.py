"""WidgetState aggregate (contracts_v2.md §1-2, V2B).

GET /widget/state is a pure read: it never triggers generation and never
writes. A missing daily receipt is reported as PENDING + receipt_stale=false
(missing = unknown, not an error); confirmation kinds with no logged events
today are omitted entirely. All derived values reuse the V1 computations
verbatim — `_age_days` for goal aging, `ModeService.current` for the open
interval's duration, `local_day_window` for the user-local day.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.db.models import User
from app.db.repositories.events import EventRepository
from app.db.repositories.goals import GoalRepository
from app.db.repositories.recaps import DirectiveRepository, RecapRepository
from app.domain.enums import (
    ConfirmationKind,
    EventType,
    GenerationStatus,
    GoalStatus,
    RecapPeriod,
)
from app.schemas.contracts import WidgetState
from app.services.daily_context import local_day_window
from app.services.goals import _age_days
from app.services.modes import ModeService

_DIRECTIVE_LINE_MAX = 120


def _directive_line(content: str) -> str:
    """Single line, <=120 chars, server-truncated (contracts_v2 §1)."""
    return " ".join(content.split())[:_DIRECTIVE_LINE_MAX]


class WidgetStateService:
    def __init__(self, session: Session):
        self.session = session
        self.events = EventRepository(session)
        self.goals = GoalRepository(session)
        self.recaps = RecapRepository(session)
        self.directives = DirectiveRepository(session)

    def build(self, user: User) -> WidgetState:
        tz = ZoneInfo(user.timezone)
        now = datetime.now(UTC)
        today = now.astimezone(tz).date()
        start, end = local_day_window(tz, today)

        day_events = self.events.list_between(user.id, start, end)
        confirmations = {
            kind: sum(
                1
                for e in day_events
                if e.type == EventType.CONFIRMATION and e.kind == kind
            )
            for kind in ConfirmationKind
        }
        confirmations = {k: n for k, n in confirmations.items() if n}
        quiet_moments = sum(
            1 for e in day_events if e.type == EventType.QUIET_MOMENT
        )

        active_goals = [
            g
            for g in self.goals.list_for_user(user.id)
            if g.status == GoalStatus.ACTIVE
        ]
        oldest_age = (
            max(_age_days(g.created_at, tz, now) for g in active_goals)
            if active_goals
            else None
        )

        directive = self.directives.get_for_date(user.id, today)
        receipt = self.recaps.get_for_period(user.id, RecapPeriod.DAILY, today)

        return WidgetState(
            generated_at=now,
            mode=ModeService(self.session).current(user.id),
            today_confirmations=confirmations,
            quiet_moments_today=quiet_moments,
            goals_active=len(active_goals),
            oldest_goal_age_days=oldest_age,
            directive_line=_directive_line(directive.content) if directive else None,
            directive_status=directive.status if directive else None,
            receipt_status=receipt.status if receipt else GenerationStatus.PENDING,
            receipt_stale=bool(receipt.stale) if receipt else False,
        )

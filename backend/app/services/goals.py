"""Rule of 3 goal lifecycle (contracts.md GoalItem, D14).

Cap enforcement is the locked D14 mechanism: inside one transaction, take a
per-user row lock (`SELECT ... FOR UPDATE` on the user row), count ACTIVE
goals, reject the insert with 409 GOAL_CAP_REACHED at 3. No client-side
enforcement.

`age_days` is computed at read time from created_at converted into the
user's IANA timezone — never a stored counter.
"""

import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.db.models import Goal, User
from app.db.repositories.goals import GoalRepository
from app.domain import errors
from app.domain.enums import GoalStatus
from app.schemas.contracts import GoalItem
from app.services.modes import _aware

MAX_ACTIVE_GOALS = 3


def _age_days(created_at: datetime, tz: ZoneInfo, now: datetime) -> int:
    created_local = _aware(created_at).astimezone(tz).date()
    today_local = now.astimezone(tz).date()
    return max(0, (today_local - created_local).days)


def _to_item(goal: Goal, tz: ZoneInfo, now: datetime) -> GoalItem:
    return GoalItem(
        id=goal.id,
        title=goal.title,
        status=goal.status,
        created_at=_aware(goal.created_at),
        resolved_at=_aware(goal.resolved_at) if goal.resolved_at else None,
        age_days=_age_days(goal.created_at, tz, now),
    )


class GoalService:
    def __init__(self, session: Session):
        self.session = session
        self.goals = GoalRepository(session)

    def list(self, user: User) -> list[GoalItem]:
        tz = ZoneInfo(user.timezone)
        now = datetime.now(UTC)
        return [_to_item(g, tz, now) for g in self.goals.list_for_user(user.id)]

    def add(self, user: User, title: str) -> GoalItem:
        title = title.strip()
        if not title:
            raise errors.validation("title must be a non-empty string")
        if len(title) > 500:
            raise errors.validation("title must be 500 characters or fewer")

        # D14: serialize on the user row, then count under the lock.
        self.goals.lock_user(user.id)
        active = self.goals.count_active(user.id)
        if active >= MAX_ACTIVE_GOALS:
            raise errors.goal_cap_reached(active)

        goal = self.goals.add(Goal(user_id=user.id, title=title, status=GoalStatus.ACTIVE))
        self.session.commit()
        return _to_item(goal, ZoneInfo(user.timezone), datetime.now(UTC))

    def _resolve(self, user: User, goal_id: uuid.UUID, status: GoalStatus) -> GoalItem:
        goal = self.goals.get_for_user(user.id, goal_id)
        if goal is None or goal.status != GoalStatus.ACTIVE:
            raise errors.not_found("Goal not found")
        goal.status = status
        goal.resolved_at = datetime.now(UTC)
        self.session.commit()
        return _to_item(goal, ZoneInfo(user.timezone), datetime.now(UTC))

    def complete(self, user: User, goal_id: uuid.UUID) -> GoalItem:
        return self._resolve(user, goal_id, GoalStatus.COMPLETED)

    def retire(self, user: User, goal_id: uuid.UUID) -> GoalItem:
        return self._resolve(user, goal_id, GoalStatus.RETIRED)

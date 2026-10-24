import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Goal, User
from app.domain.enums import GoalStatus


class GoalRepository:
    def __init__(self, session: Session):
        self.session = session

    def lock_user(self, user_id: uuid.UUID) -> User:
        """Per-user row lock for serialized Rule-of-3 enforcement (D14)."""
        return self.session.execute(
            select(User).where(User.id == user_id).with_for_update()
        ).scalar_one()

    def count_active(self, user_id: uuid.UUID) -> int:
        return self.session.execute(
            select(func.count())
            .select_from(Goal)
            .where(Goal.user_id == user_id, Goal.status == GoalStatus.ACTIVE)
        ).scalar_one()

    def list_for_user(self, user_id: uuid.UUID) -> list[Goal]:
        return list(
            self.session.execute(
                select(Goal).where(Goal.user_id == user_id).order_by(Goal.created_at)
            ).scalars()
        )

    def add(self, goal: Goal) -> Goal:
        self.session.add(goal)
        self.session.flush()
        return goal

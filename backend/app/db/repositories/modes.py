import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ModeIntervalRow


class ModeIntervalRepository:
    def __init__(self, session: Session):
        self.session = session

    def current(self, user_id: uuid.UUID) -> ModeIntervalRow | None:
        return self.session.execute(
            select(ModeIntervalRow)
            .where(ModeIntervalRow.user_id == user_id, ModeIntervalRow.ended_at.is_(None))
            .order_by(ModeIntervalRow.started_at.desc())
            .limit(1)
        ).scalar_one_or_none()

    def list_overlapping(
        self, user_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[ModeIntervalRow]:
        """Intervals intersecting the half-open [start, end) window,
        including the still-open interval."""
        return list(
            self.session.execute(
                select(ModeIntervalRow)
                .where(
                    ModeIntervalRow.user_id == user_id,
                    ModeIntervalRow.started_at < end,
                    (ModeIntervalRow.ended_at.is_(None))
                    | (ModeIntervalRow.ended_at > start),
                )
                .order_by(ModeIntervalRow.started_at)
            ).scalars()
        )

    def list_for_user(self, user_id: uuid.UUID, limit: int = 100) -> list[ModeIntervalRow]:
        return list(
            self.session.execute(
                select(ModeIntervalRow)
                .where(ModeIntervalRow.user_id == user_id)
                .order_by(ModeIntervalRow.started_at.desc())
                .limit(limit)
            ).scalars()
        )

    def add(self, row: ModeIntervalRow) -> ModeIntervalRow:
        self.session.add(row)
        self.session.flush()
        return row

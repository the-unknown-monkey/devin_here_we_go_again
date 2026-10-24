import uuid
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MorningDirectiveRow, RecapRow
from app.domain.enums import RecapPeriod


class RecapRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_for_period(
        self, user_id: uuid.UUID, period_type: RecapPeriod, period_start: date
    ) -> RecapRow | None:
        return self.session.execute(
            select(RecapRow).where(
                RecapRow.user_id == user_id,
                RecapRow.period_type == period_type,
                RecapRow.period_start == period_start,
            )
        ).scalar_one_or_none()

    def list_daily_between(
        self, user_id: uuid.UUID, start: date, end: date
    ) -> list[RecapRow]:
        """Stored DAILY recaps with period_start in [start, end], ordered.
        This is the only history the weekly chain consumes — never raw
        event rows."""
        return list(
            self.session.execute(
                select(RecapRow)
                .where(
                    RecapRow.user_id == user_id,
                    RecapRow.period_type == RecapPeriod.DAILY,
                    RecapRow.period_start >= start,
                    RecapRow.period_start <= end,
                )
                .order_by(RecapRow.period_start)
            ).scalars()
        )

    def latest_daily_before(
        self, user_id: uuid.UUID, for_date: date
    ) -> RecapRow | None:
        """Most recent non-stale DAILY recap strictly before `for_date`."""
        return self.session.execute(
            select(RecapRow)
            .where(
                RecapRow.user_id == user_id,
                RecapRow.period_type == RecapPeriod.DAILY,
                RecapRow.period_start < for_date,
                RecapRow.stale.is_(False),
            )
            .order_by(RecapRow.period_start.desc())
            .limit(1)
        ).scalar_one_or_none()

    def recent_dailies(self, user_id: uuid.UUID, limit: int = 3) -> list[RecapRow]:
        """Most recent non-stale DAILY recaps, newest first."""
        return list(
            self.session.execute(
                select(RecapRow)
                .where(
                    RecapRow.user_id == user_id,
                    RecapRow.period_type == RecapPeriod.DAILY,
                    RecapRow.stale.is_(False),
                )
                .order_by(RecapRow.period_start.desc())
                .limit(limit)
            ).scalars()
        )

    def add(self, recap: RecapRow) -> RecapRow:
        self.session.add(recap)
        self.session.flush()
        return recap


class DirectiveRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_for_date(self, user_id: uuid.UUID, for_date: date) -> MorningDirectiveRow | None:
        return self.session.execute(
            select(MorningDirectiveRow).where(
                MorningDirectiveRow.user_id == user_id,
                MorningDirectiveRow.for_date == for_date,
            )
        ).scalar_one_or_none()

    def add(self, directive: MorningDirectiveRow) -> MorningDirectiveRow:
        self.session.add(directive)
        self.session.flush()
        return directive

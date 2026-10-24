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

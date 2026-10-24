import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Event


class EventRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_idempotency_key(self, user_id: uuid.UUID, key: str) -> Event | None:
        return self.session.execute(
            select(Event).where(
                Event.user_id == user_id, Event.idempotency_key == key
            )
        ).scalar_one_or_none()

    def add(self, event: Event) -> Event:
        self.session.add(event)
        self.session.flush()
        return event

    def list_between(
        self, user_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[Event]:
        return list(
            self.session.execute(
                select(Event)
                .where(
                    Event.user_id == user_id,
                    Event.occurred_at >= start,
                    Event.occurred_at < end,
                )
                .order_by(Event.occurred_at)
            ).scalars()
        )

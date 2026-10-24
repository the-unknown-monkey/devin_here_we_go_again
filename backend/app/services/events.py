"""Event ingestion rules (contracts.md EventIn).

Accepted via POST /events: CONFIRMATION (kind required), QUIET_MOMENT, and
MODE_TRANSITION (delegated to ModeService so interval ordering stays
consistent). MEDIA_CAPTURED rows are created by the media pipeline
(HWGA05), never by client event posts.

Idempotent on (user_id, idempotency_key): duplicate taps return the stored
event instead of creating a second row.
"""

import uuid
from datetime import UTC, datetime
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import Event, User
from app.db.repositories.events import EventRepository
from app.domain import errors
from app.domain.enums import EventType
from app.schemas.contracts import EventIn
from app.services.modes import ModeService, _aware


def serialize_event(e: Event) -> dict:
    return {
        "id": str(e.id),
        "type": e.type.value,
        "kind": e.kind.value if e.kind else None,
        "mode": e.mode.value if e.mode else None,
        "occurred_at": _aware(e.occurred_at).isoformat(),
        "idempotency_key": e.idempotency_key,
    }


def _validate(payload: EventIn) -> None:
    if payload.type == EventType.CONFIRMATION:
        if payload.kind is None:
            raise errors.validation("kind is required for CONFIRMATION events")
        if payload.mode is not None:
            raise errors.validation("mode is only valid for MODE_TRANSITION events")
    elif payload.type == EventType.QUIET_MOMENT:
        if payload.kind is not None or payload.mode is not None:
            raise errors.validation("QUIET_MOMENT takes neither kind nor mode")
    elif payload.type == EventType.MODE_TRANSITION:
        if payload.mode is None:
            raise errors.validation("mode is required for MODE_TRANSITION events")
        if payload.kind is not None:
            raise errors.validation("kind is only valid for CONFIRMATION events")
    elif payload.type == EventType.MEDIA_CAPTURED:
        raise errors.validation("MEDIA_CAPTURED is recorded by the media pipeline, not /events")
    if not payload.idempotency_key.strip():
        raise errors.validation("idempotency_key must be a non-empty string")


class EventService:
    def __init__(self, session: Session):
        self.session = session
        self.events = EventRepository(session)

    def ingest(self, user: User, payload: EventIn) -> tuple[Event, bool]:
        """Returns (event, created). created=False on idempotent replay."""
        _validate(payload)

        existing = self.events.get_by_idempotency_key(user.id, payload.idempotency_key)
        if existing is not None:
            return existing, False

        if payload.type == EventType.MODE_TRANSITION:
            event, _ = ModeService(self.session).transition(
                user.id, payload.mode, payload.occurred_at, payload.idempotency_key
            )
            self._mark_stale_recap(user, event.occurred_at)
            self.session.commit()
            return event, True

        event = Event(
            user_id=user.id,
            type=payload.type,
            kind=payload.kind,
            occurred_at=_aware(payload.occurred_at) if payload.occurred_at else datetime.now(UTC),
            idempotency_key=payload.idempotency_key,
        )
        try:
            self.events.add(event)
            self._mark_stale_recap(user, event.occurred_at)
            self.session.commit()
        except IntegrityError:
            # Racing duplicate tap lost the unique-constraint check — the
            # first insert wins and this replay returns that row.
            self.session.rollback()
            existing = self.events.get_by_idempotency_key(user.id, payload.idempotency_key)
            if existing is None:
                raise
            return existing, False
        return event, True

    def _mark_stale_recap(self, user: User, occurred_at: datetime) -> None:
        # Imported here to avoid a service import cycle.
        from app.services.recaps import RecapService

        RecapService(self.session).mark_stale_for_local_date(user, occurred_at)

    def window(
        self, user: User, start: datetime | None, end: datetime | None
    ) -> tuple[datetime, datetime]:
        """Default timeline window = the user's local day (their timezone)."""
        tz = ZoneInfo(user.timezone)
        if end is None:
            end = datetime.now(UTC)
        if start is None:
            start = end.astimezone(tz).replace(hour=0, minute=0, second=0, microsecond=0)
        return _aware(start), _aware(end)

    def timeline(
        self, user: User, start: datetime | None, end: datetime | None
    ) -> list[Event]:
        start, end = self.window(user, start, end)
        return self.events.list_between(user.id, start, end)

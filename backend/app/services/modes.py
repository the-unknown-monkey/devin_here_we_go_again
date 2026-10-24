"""Mode interval rules — backend is the authority for ordering and durations
(TRD §5, contracts.md ModeInterval). Rest (PURE_FUN_RECOVERY) is a valid,
positive mode; no streak or shame semantics exist here.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import Event, ModeIntervalRow
from app.db.repositories.events import EventRepository
from app.db.repositories.modes import ModeIntervalRepository
from app.domain import errors
from app.domain.enums import EventType, UserMode
from app.schemas.contracts import ModeInterval


def _aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=UTC)


def _to_contract(row: ModeIntervalRow, now: datetime) -> ModeInterval:
    """Derive duration_min deterministically: ended intervals use their
    stored bounds; the open interval uses elapsed time at read."""
    if row.ended_at is not None:
        duration_min = int((_aware(row.ended_at) - _aware(row.started_at)).total_seconds() // 60)
    else:
        duration_min = int((now - _aware(row.started_at)).total_seconds() // 60)
    return ModeInterval(
        mode=row.mode,
        started_at=_aware(row.started_at),
        ended_at=_aware(row.ended_at) if row.ended_at else None,
        duration_min=duration_min,
    )


class ModeService:
    def __init__(self, session: Session):
        self.session = session
        self.intervals = ModeIntervalRepository(session)
        self.events = EventRepository(session)

    def current(self, user_id: uuid.UUID) -> ModeInterval | None:
        row = self.intervals.current(user_id)
        if row is None:
            return None
        return _to_contract(row, datetime.now(UTC))

    def list_intervals(self, user_id: uuid.UUID, limit: int = 100) -> list[ModeInterval]:
        now = datetime.now(UTC)
        return [_to_contract(r, now) for r in self.intervals.list_for_user(user_id, limit)]

    def transition(
        self,
        user_id: uuid.UUID,
        mode: UserMode,
        occurred_at: datetime | None,
        idempotency_key: str | None,
    ) -> tuple[Event, ModeInterval]:
        """Enter `mode`. Validates ordering, closes the open interval, and
        records the MODE_TRANSITION event. Re-entering the current mode is
        not a transition."""
        at = _aware(occurred_at) if occurred_at else datetime.now(UTC)
        current = self.intervals.current(user_id)

        if current is not None:
            if current.mode == mode:
                raise errors.invalid_mode_transition(
                    f"Already in {mode.value}; pick the other mode to switch."
                )
            if at < _aware(current.started_at):
                raise errors.invalid_mode_transition(
                    "Transition time is before the current mode started."
                )
            current.ended_at = at
            self.session.flush()

        row = ModeIntervalRow(user_id=user_id, mode=mode, started_at=at)
        self.intervals.add(row)

        event = Event(
            user_id=user_id,
            type=EventType.MODE_TRANSITION,
            mode=mode,
            occurred_at=at,
            idempotency_key=idempotency_key or f"mode:{row.id}",
        )
        self.events.add(event)
        self.session.commit()
        return event, _to_contract(row, datetime.now(UTC))

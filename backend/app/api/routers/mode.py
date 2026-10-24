"""GET/POST /mode — current mode and validated transitions (contracts §3).
Ordering and durations are deterministic backend rules (ModeService)."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import require_auth
from app.db.models import User
from app.db.repositories.events import EventRepository
from app.db.session import get_session
from app.domain.enums import UserMode
from app.domain.errors import DomainError
from app.schemas.contracts import ModeInterval
from app.services.events import serialize_event
from app.services.modes import ModeService

router = APIRouter()


class ModeTransitionIn(BaseModel):
    mode: UserMode
    occurred_at: Optional[datetime] = None
    idempotency_key: Optional[str] = None


@router.get("/mode")
def get_mode(
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
):
    svc = ModeService(session)
    return {
        "current": svc.current(user.id),
        "intervals": svc.list_intervals(user.id),
    }


@router.post("/mode", response_model=None)
def post_mode(
    payload: ModeTransitionIn,
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
):
    svc = ModeService(session)
    try:
        if payload.idempotency_key:
            existing = EventRepository(session).get_by_idempotency_key(
                user.id, payload.idempotency_key
            )
            if existing is not None:
                return {
                    "event": serialize_event(existing),
                    "current": svc.current(user.id),
                }
        event, current = svc.transition(
            user.id, payload.mode, payload.occurred_at, payload.idempotency_key
        )
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.payload()) from exc
    return {"event": serialize_event(event), "current": current}

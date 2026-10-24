"""Event ingest + private timeline (contracts.md §3: POST /events,
GET /timeline). Routers parse HTTP and delegate; domain rules live in
app.services.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from app.core.security import require_auth
from app.db.models import User
from app.db.session import get_session
from app.domain.errors import DomainError
from app.api.routers.media import get_storage
from app.schemas.contracts import EventIn
from app.services.events import EventService, serialize_event
from app.services.media import MediaService, serialize_media

router = APIRouter()


@router.post("/events", status_code=201)
def post_event(
    payload: EventIn,
    response: Response,
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
):
    try:
        event, created = EventService(session).ingest(user, payload)
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.payload()) from exc
    if not created:
        response.status_code = 200
    return serialize_event(event)


@router.get("/timeline")
def get_timeline(
    from_: datetime | None = Query(default=None, alias="from"),
    to: datetime | None = Query(default=None),
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
    storage=Depends(get_storage),
):
    service = EventService(session)
    start, end = service.window(user, from_, to)
    events = service.timeline(user, start, end)
    media = MediaService(session, storage).timeline_media(user, start, end)
    return {
        "events": [serialize_event(e) for e in events],
        "media": [serialize_media(m) for m in media],
    }

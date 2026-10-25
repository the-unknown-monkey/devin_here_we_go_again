"""/widget — home-screen widget aggregate (contracts_v2.md §2, V2B).

GET /widget/state returns the locked WidgetState JSON (~1 KB, no media
refs, no narrative). It is a pure read: bearer-gated like every route
except /health, and it NEVER triggers generation — a missing receipt is
reported as PENDING + receipt_stale=false per the carried missing-data rule.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import require_auth
from app.db.models import User
from app.db.session import get_session
from app.domain.errors import DomainError
from app.schemas.contracts import WidgetState
from app.services.widget_state import WidgetStateService

router = APIRouter()


@router.get("/widget/state", response_model=WidgetState)
def get_widget_state(
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
):
    try:
        return WidgetStateService(session).build(user)
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.payload()) from exc

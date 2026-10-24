"""/directive — next-day morning directive (contracts.md §3, HWGA07).

GET /directive/today returns today's MorningDirective, generating it
idempotently on first open (unique on (user_id, for_date)). `shown_at`
marks first display — reopening the app never regenerates.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.agents.providers.gemini import NarrativeProvider
from app.api.routers.recaps import provider_override
from app.core.security import require_auth
from app.db.models import User
from app.db.session import get_session
from app.domain.errors import DomainError
from app.schemas.contracts import MorningDirective
from app.services.directives import DirectiveService

router = APIRouter()


@router.get("/directive/today", response_model=MorningDirective)
def get_today(
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
    provider: NarrativeProvider | None = Depends(provider_override),
):
    try:
        return DirectiveService(session, provider=provider).get_or_generate_today(user)
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.payload()) from exc

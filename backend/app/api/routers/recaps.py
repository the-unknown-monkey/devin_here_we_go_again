"""/recaps — nightly receipt fetch + internal job trigger (contracts.md §3).

GET /recaps?period=DAILY&date= returns the stored receipt, generating it
idempotently on first fetch (and regenerating a stale one after backfill).
GET /recaps?period=WEEKLY&date= does the same for the ISO week containing
the date, consuming stored DAILY recaps only. MONTHLY/YEARLY stay honest
404s — contract-level only, generation is post-V1.
POST /internal/run/{daily|weekly} is the authenticated job trigger for the
local scheduler/manual runs; anything else is an honest NOT_FOUND.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.agents.providers.gemini import NarrativeProvider
from app.core.security import require_auth
from app.db.models import User
from app.db.session import get_session
from app.domain.enums import RecapPeriod
from app.domain.errors import DomainError
from app.schemas.contracts import Recap
from app.services.recaps import RecapService

router = APIRouter()

# Injectable in tests: app.dependency_overrides[provider_override].
def provider_override() -> NarrativeProvider | None:
    return None


def _service(
    session: Session, provider: NarrativeProvider | None
) -> RecapService:
    return RecapService(session, provider=provider)


@router.get("/recaps", response_model=Recap)
def get_recap(
    period: RecapPeriod = Query(default=RecapPeriod.DAILY),
    date_: Optional[date] = Query(default=None, alias="date"),
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
    provider: NarrativeProvider | None = Depends(provider_override),
):
    try:
        return _service(session, provider).get_or_generate(user, period, date_)
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.payload()) from exc


@router.post("/internal/run/{job}", response_model=Recap)
def run_job(
    job: str,
    date_: Optional[date] = Query(default=None, alias="date"),
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
    provider: NarrativeProvider | None = Depends(provider_override),
):
    if job not in ("daily", "weekly"):
        raise HTTPException(
            status_code=404,
            detail={"code": "NOT_FOUND", "message": f"Unknown job {job!r}", "details": {}},
        )
    period = RecapPeriod.DAILY if job == "daily" else RecapPeriod.WEEKLY
    try:
        return _service(session, provider).get_or_generate(user, period, date_)
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.payload()) from exc

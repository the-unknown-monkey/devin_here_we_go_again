"""GET /me — minimal authenticated profile probe.

Added in HWGA03 so the phone can prove a real bearer-token request; /health
is unauthenticated by contract so it cannot evidence auth on its own.
"""

from fastapi import APIRouter, Depends

from app.core.security import require_auth
from app.db.models import User

router = APIRouter()


@router.get("/me")
def me(user: User = Depends(require_auth)) -> dict:
    return {"user_id": str(user.id), "timezone": user.timezone}

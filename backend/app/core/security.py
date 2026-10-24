"""Single-user bearer-token auth (D07).

Tokens are provisioned by `app.cli provision-token`, stored in `auth_tokens`
as HMAC-SHA256(pepper, token). Plaintext tokens never touch the DB or logs.
Every route except GET /health depends on `require_auth`.
"""

import hashlib
import hmac
import secrets

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.models import AuthToken, User
from app.db.session import get_session

_bearer = HTTPBearer(auto_error=False)


def hash_token(token: str, pepper: str) -> str:
    return hmac.new(pepper.encode(), token.encode(), hashlib.sha256).hexdigest()


def generate_token() -> str:
    return secrets.token_urlsafe(32)


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail={"code": "UNAUTHORIZED", "message": "Missing or invalid credentials", "details": {}},
    )


def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    digest = hash_token(credentials.credentials, settings.auth_token_pepper)
    row = session.execute(
        select(AuthToken).where(AuthToken.token_hash == digest)
    ).scalar_one_or_none()
    if row is None:
        raise _unauthorized()
    return session.get(User, row.user_id)

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import AuthToken, User


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, user_id: uuid.UUID) -> User | None:
        return self.session.get(User, user_id)

    def get_or_create_single_user(self, timezone: str) -> User:
        user = self.session.execute(select(User).limit(1)).scalar_one_or_none()
        if user is None:
            user = User(timezone=timezone)
            self.session.add(user)
            self.session.flush()
        return user


class AuthTokenRepository:
    def __init__(self, session: Session):
        self.session = session

    def add(self, user_id: uuid.UUID, token_hash: str) -> AuthToken:
        row = AuthToken(user_id=user_id, token_hash=token_hash)
        self.session.add(row)
        self.session.flush()
        return row

    def get_by_hash(self, token_hash: str) -> AuthToken | None:
        return self.session.execute(
            select(AuthToken).where(AuthToken.token_hash == token_hash)
        ).scalar_one_or_none()

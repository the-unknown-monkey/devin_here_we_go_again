"""Test harness. All DB fixtures point at TEST_DATABASE_URL (disposable,
tmpfs-backed Postgres on 55533). A hard guard refuses to run if the test
URL equals the dev DATABASE_URL."""

import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import Settings, get_settings
from app.core.security import generate_token, hash_token, require_auth
from app.db.models import AuthToken, User
from app.db.session import get_session
from app.main import create_app

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://hwga:hwga@127.0.0.1:55533/hwga_test",
)
TEST_PEPPER = "test-only-pepper-not-a-real-secret!!"

os.environ["ALEMBIC_DATABASE_URL"] = TEST_DATABASE_URL


@pytest.fixture(scope="session")
def test_engine():
    settings = Settings(
        database_url="postgresql+psycopg://hwga:hwga@127.0.0.1:55532/hwga",
        test_database_url=TEST_DATABASE_URL,
        auth_token_pepper=TEST_PEPPER,
    )
    # Isolation guard is enforced inside Settings(); belt-and-suspenders here:
    assert settings.test_database_url != settings.database_url
    engine = create_engine(settings.test_database_url, pool_pre_ping=True)
    # Reset schema so migrations apply cleanly every run (disposable DB).
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    yield engine
    engine.dispose()


@pytest.fixture()
def session(test_engine):
    factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    with factory() as s:
        yield s
        s.rollback()


@pytest.fixture()
def media_root(tmp_path, monkeypatch):
    """Per-test isolated media storage root (never the dev data/ dir)."""
    root = tmp_path / "media"
    monkeypatch.setenv("MEDIA_STORAGE_ROOT", str(root))
    return root


@pytest.fixture()
def client(session, media_root, monkeypatch):
    monkeypatch.setenv("AUTH_TOKEN_PEPPER", TEST_PEPPER)
    get_settings.cache_clear()

    app = create_app()

    def _override_session():
        yield session

    app.dependency_overrides[get_session] = _override_session

    # Probe route so the foundation can verify the auth dependency without
    # pre-implementing later-phase routers.
    @app.get("/_probe")
    def _probe(user=Depends(require_auth)):
        return {"user_id": str(user.id)}

    with TestClient(app) as c:
        yield c


@pytest.fixture()
def issued_token(session):
    user = User(timezone="Asia/Kolkata")
    session.add(user)
    session.flush()
    token = generate_token()
    session.add(AuthToken(user_id=user.id, token_hash=hash_token(token, TEST_PEPPER)))
    # Commit so domain-service rollbacks (e.g. after a 422 DomainError)
    # can't wipe the still-uncommitted token row mid-test.
    session.commit()
    return token

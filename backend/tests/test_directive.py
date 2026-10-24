"""HWGA07: morning directive tests — mocked provider, real DB + graph.

Covers: no stored recap (honest fallback), provider failure -> FALLBACK,
guard rejection of coercive/invented content, idempotent generation and
retries, `shown_at` display dedupe, local-date rollover producing a new
directive, and the /directive/today API contract.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.routers import recaps as recaps_router
from app.agents.providers.gemini import ProviderError, ProviderErrorKind
from app.agents.schemas.directive import DirectiveCandidate
from app.db.models import RecapRow, User
from app.db.session import get_session
from app.domain.enums import GenerationStatus, GoalStatus, RecapPeriod
from app.main import create_app
from app.services.directives import DirectiveService

YESTERDAY = date(2026, 10, 24)
FOR_DATE = date(2026, 10, 25)
# 2026-10-25 07:00 IST == 2026-10-25 01:30 UTC
NOW_UTC = datetime(2026, 10, 25, 1, 30, tzinfo=UTC)


@pytest.fixture()
def user(session):
    u = User(timezone="Asia/Kolkata")
    session.add(u)
    session.commit()
    return u


@pytest.fixture()
def authed(session):
    from app.core.security import generate_token, hash_token
    from app.db.models import AuthToken
    from tests.conftest import TEST_PEPPER

    u = User(timezone="Asia/Kolkata")
    session.add(u)
    session.flush()
    token = generate_token()
    session.add(AuthToken(user_id=u.id, token_hash=hash_token(token, TEST_PEPPER)))
    session.commit()
    return token, u


def _stored_recap(session, user, directive="Take one gentle step tomorrow."):
    row = RecapRow(
        user_id=user.id,
        period_type=RecapPeriod.DAILY,
        period_start=YESTERDAY,
        period_end=YESTERDAY,
        narrative="You logged 2 glasses of water and rested.",
        insights=[],
        highlight_media_ids=[],
        directive_for_next_cycle=directive,
        source_recap_ids=[],
        status=GenerationStatus.GENERATED,
        stale=False,
    )
    session.add(row)
    session.commit()
    return row


def _stored_goal(session, user, title="Ship the demo"):
    from app.db.models import Goal

    g = Goal(user_id=user.id, title=title, status=GoalStatus.ACTIVE)
    session.add(g)
    session.commit()
    return g


class GoodDirectiveProvider:
    def __init__(self, content="Open the vault and keep one moment today."):
        self.calls = 0
        self.contexts = []
        self._content = content

    def generate_directive(self, context):
        self.calls += 1
        self.contexts.append(context)
        return DirectiveCandidate(content=self._content)


class FailingProvider:
    def __init__(self, kind=ProviderErrorKind.TIMEOUT):
        self.calls = 0
        self._kind = kind

    def generate_directive(self, context):
        self.calls += 1
        raise ProviderError(self._kind, "boom")


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------

def test_generated_directive_persisted_with_source_recap(session, user):
    recap = _stored_recap(session, user)
    provider = GoodDirectiveProvider()
    directive = DirectiveService(session, provider=provider).get_or_generate_today(
        user, now=NOW_UTC
    )
    assert directive.status == GenerationStatus.GENERATED
    assert directive.for_date == FOR_DATE
    assert directive.source_recap_id == recap.id
    assert "moment" in directive.content
    assert directive.shown_at is not None


def test_no_recap_still_yields_honest_directive(session, user):
    provider = FailingProvider(ProviderErrorKind.NO_KEY)
    directive = DirectiveService(session, provider=provider).get_or_generate_today(
        user, now=NOW_UTC
    )
    assert directive.status == GenerationStatus.FALLBACK
    assert directive.source_recap_id is None
    # Nothing is asserted about yesterday — no events were invented.
    lowered = directive.content.lower()
    for word in ("lazy", "failed", "missed", "yesterday"):
        assert word not in lowered


def test_fallback_prefers_stored_recap_directive(session, user):
    _stored_recap(session, user, directive="One small step on the demo today.")
    provider = FailingProvider()
    directive = DirectiveService(session, provider=provider).get_or_generate_today(
        user, now=NOW_UTC
    )
    assert directive.status == GenerationStatus.FALLBACK
    assert directive.content == "One small step on the demo today."


def test_provider_failure_falls_back(session, user):
    _stored_goal(session, user)
    provider = FailingProvider(ProviderErrorKind.QUOTA)
    directive = DirectiveService(session, provider=provider).get_or_generate_today(
        user, now=NOW_UTC
    )
    assert directive.status == GenerationStatus.FALLBACK
    assert "Ship the demo" in directive.content


@pytest.mark.parametrize(
    "bad",
    [
        "You must finish everything today — no excuses!",
        "You drank 5 waters yesterday, do 6 today.",  # invented quantities
    ],
)
def test_guard_rejects_coercive_or_invented_content(session, user, bad):
    _stored_recap(session, user)
    provider = GoodDirectiveProvider(content=bad)
    directive = DirectiveService(session, provider=provider).get_or_generate_today(
        user, now=NOW_UTC
    )
    assert directive.status == GenerationStatus.FALLBACK
    assert directive.content != bad


def test_idempotent_repeat_open_never_regenerates(session, user):
    _stored_recap(session, user)
    provider = GoodDirectiveProvider()
    svc = DirectiveService(session, provider=provider)
    first = svc.get_or_generate_today(user, now=NOW_UTC)
    second = svc.get_or_generate_today(user, now=NOW_UTC + timedelta(hours=3))
    assert first.id == second.id
    assert first.shown_at == second.shown_at  # display dedupe, not re-stamped
    assert provider.calls == 1


def test_new_local_date_generates_new_directive(session, user):
    provider = GoodDirectiveProvider()
    svc = DirectiveService(session, provider=provider)
    today = svc.get_or_generate_today(user, now=NOW_UTC)
    tomorrow = svc.get_or_generate_today(user, now=NOW_UTC + timedelta(days=1))
    assert today.id != tomorrow.id
    assert today.for_date == FOR_DATE
    assert tomorrow.for_date == FOR_DATE + timedelta(days=1)
    assert provider.calls == 2


def test_timezone_rollover_uses_user_local_date(session):
    """23:30 UTC is still the 25th in UTC but already the 26th in IST."""
    u = User(timezone="Asia/Kolkata")
    session.add(u)
    session.commit()
    provider = GoodDirectiveProvider()
    directive = DirectiveService(session, provider=provider).get_or_generate_today(
        u, now=datetime(2026, 10, 25, 23, 30, tzinfo=UTC)
    )
    assert directive.for_date == date(2026, 10, 26)


# ---------------------------------------------------------------------------
# API-level tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def directive_client(session, media_root, monkeypatch):
    from app.core.config import get_settings
    from tests.conftest import TEST_PEPPER

    monkeypatch.setenv("AUTH_TOKEN_PEPPER", TEST_PEPPER)
    get_settings.cache_clear()
    app = create_app()

    def _override_session():
        yield session

    provider = GoodDirectiveProvider()
    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[recaps_router.provider_override] = lambda: provider

    with TestClient(app) as c:
        c.provider = provider  # type: ignore[attr-defined]
        yield c


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_directive_today_route(directive_client, session, authed):
    token, user = authed
    _stored_recap(session, user)
    res = directive_client.get("/directive/today", headers=_auth(token))
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "GENERATED"
    assert body["content"]
    assert body["shown_at"] is not None
    # Second open: same directive, same shown_at, no regeneration.
    res2 = directive_client.get("/directive/today", headers=_auth(token))
    assert res2.json()["id"] == body["id"]
    assert res2.json()["shown_at"] == body["shown_at"]
    assert directive_client.provider.calls == 1


def test_directive_requires_auth(directive_client):
    assert directive_client.get("/directive/today").status_code == 401

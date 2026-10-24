"""HWGA06: receipt workflow tests — mocked provider, real DB + graph.

Covers the deterministic pipeline end to end: GENERATED on valid grounded
output; FALLBACK on schema-invalid, unsupported-claim, timeout, and quota
paths; idempotent re-fetch; stale regeneration after backfilled events;
and the /recaps + /internal/run API contract.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.api.routers import recaps as recaps_router
from app.agents.providers.gemini import ProviderError, ProviderErrorKind
from app.agents.schemas.receipt import CandidateInsight, RecapCandidate
from app.db.models import Event, User
from app.db.session import get_session
from app.domain.enums import (
    ConfirmationKind,
    EventType,
    GenerationStatus,
    RecapPeriod,
)
from app.main import create_app
from app.services.recaps import RecapService

LOCAL_DATE = date(2026, 10, 20)
# IST local day -> UTC window (see test_daily_context).
T1 = datetime(2026, 10, 19, 20, 0, tzinfo=UTC)
T2 = datetime(2026, 10, 20, 10, 0, tzinfo=UTC)


@pytest.fixture()
def user(session):
    u = User(timezone="Asia/Kolkata")
    session.add(u)
    session.commit()
    return u


@pytest.fixture()
def authed(session):
    """User + issued bearer token for API-level tests."""
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


def _seed_day_events(session, user):
    e1 = Event(
        user_id=user.id,
        type=EventType.CONFIRMATION,
        kind=ConfirmationKind.WATER,
        occurred_at=T1,
        idempotency_key=f"k-{uuid.uuid4()}",
    )
    e2 = Event(
        user_id=user.id,
        type=EventType.QUIET_MOMENT,
        occurred_at=T2,
        idempotency_key=f"k-{uuid.uuid4()}",
    )
    session.add_all([e1, e2])
    session.commit()
    return e1, e2


@pytest.fixture()
def day_events(session, user):
    return _seed_day_events(session, user)


class GoodProvider:
    """Grounded candidate citing only real evidence ids."""

    def __init__(self):
        self.calls = 0

    def generate_receipt(self, context):
        self.calls += 1
        eid = str(context.evidence_event_ids[0])
        return RecapCandidate(
            narrative=f"A day with {context.quiet_moments} quiet moment and "
            f"{context.confirmations.get('WATER', 0)} water on {context.local_date}.",
            insights=[
                CandidateInsight(text="You paused once for yourself.", evidence_event_ids=[eid])
            ],
            highlight_media_ids=[],
            directive_for_next_cycle="Keep the gentle rhythm tomorrow.",
        )


class FakeProvider:
    def __init__(self, behavior):
        self.behavior = behavior
        self.calls = 0

    def generate_receipt(self, context):
        self.calls += 1
        if isinstance(self.behavior, Exception):
            raise self.behavior
        return self.behavior(context)


def _unsupported_candidate(context):
    return RecapCandidate(
        narrative="You drank 99 waters and completed 3 goals in 400 minutes of focus.",
        insights=[
            CandidateInsight(
                text="Made-up claim with a fabricated id.",
                evidence_event_ids=[str(uuid.uuid4())],
            )
        ],
        highlight_media_ids=[str(uuid.uuid4())],
    )


# ---------------------------------------------------------------------------
# Service-level workflow tests
# ---------------------------------------------------------------------------

def test_generated_receipt_persisted(session, user, day_events):
    provider = GoodProvider()
    recap = RecapService(session, provider=provider).get_or_generate(
        user, RecapPeriod.DAILY, LOCAL_DATE
    )
    assert recap.status == GenerationStatus.GENERATED
    assert "quiet moment" in recap.narrative
    assert recap.period_start == LOCAL_DATE == recap.period_end
    valid = {str(e.id) for e in day_events}
    for ins in recap.insights:
        assert ins["evidence_event_ids"]
        assert set(ins["evidence_event_ids"]) <= valid
    assert provider.calls == 1


def test_idempotent_refetch_does_not_regenerate(session, user, day_events):
    provider = GoodProvider()
    svc = RecapService(session, provider=provider)
    first = svc.get_or_generate(user, RecapPeriod.DAILY, LOCAL_DATE)
    second = svc.get_or_generate(user, RecapPeriod.DAILY, LOCAL_DATE)
    assert first.id == second.id
    assert provider.calls == 1


def test_schema_invalid_output_falls_back(session, user, day_events):
    provider = FakeProvider(ProviderError(ProviderErrorKind.INVALID_OUTPUT, "bad json"))
    recap = RecapService(session, provider=provider).get_or_generate(
        user, RecapPeriod.DAILY, LOCAL_DATE
    )
    assert recap.status == GenerationStatus.FALLBACK
    assert recap.narrative  # deterministic fallback still produced a receipt
    for ins in recap.insights:
        assert set(ins["evidence_event_ids"]) <= {str(e.id) for e in day_events}


@pytest.mark.parametrize("kind", [ProviderErrorKind.TIMEOUT, ProviderErrorKind.QUOTA])
def test_timeout_and_quota_fall_back(session, user, day_events, kind):
    provider = FakeProvider(ProviderError(kind, "exhausted"))
    recap = RecapService(session, provider=provider).get_or_generate(
        user, RecapPeriod.DAILY, LOCAL_DATE
    )
    assert recap.status == GenerationStatus.FALLBACK


def test_unsupported_claims_rejected_by_fact_guard(session, user, day_events):
    provider = FakeProvider(_unsupported_candidate)
    recap = RecapService(session, provider=provider).get_or_generate(
        user, RecapPeriod.DAILY, LOCAL_DATE
    )
    # 99 waters / completed goals / 400 minutes — all contradicted by the
    # context, so the narrative is rejected and the fallback is persisted.
    assert recap.status == GenerationStatus.FALLBACK
    assert "99" not in recap.narrative


def test_partially_bad_candidate_keeps_valid_insights(session, user, day_events):
    good_id = str(day_events[0].id)

    def build(context):
        return RecapCandidate(
            narrative="A gentle, ordinary day.",
            insights=[
                CandidateInsight(text="Water was logged.", evidence_event_ids=[good_id]),
                CandidateInsight(
                    text="You drank 7 waters.",  # contradicted: only 1 logged
                    evidence_event_ids=[good_id],
                ),
                CandidateInsight(
                    text="Ghost evidence.",
                    evidence_event_ids=[str(uuid.uuid4())],
                ),
            ],
        )

    recap = RecapService(
        session, provider=FakeProvider(build)
    ).get_or_generate(user, RecapPeriod.DAILY, LOCAL_DATE)
    assert recap.status == GenerationStatus.GENERATED
    assert [i["text"] for i in recap.insights] == ["Water was logged."]


def test_backfilled_event_marks_recap_stale_and_regenerates(
    session, user, day_events
):
    provider = GoodProvider()
    svc = RecapService(session, provider=provider)
    first = svc.get_or_generate(user, RecapPeriod.DAILY, LOCAL_DATE)
    assert first.status == GenerationStatus.GENERATED

    # Late event arrives for the same local day AFTER the recap exists.
    from app.schemas.contracts import EventIn
    from app.services.events import EventService

    EventService(session).ingest(
        user,
        EventIn(
            type=EventType.CONFIRMATION,
            kind=ConfirmationKind.STRETCH,
            occurred_at=T1 + timedelta(hours=1),
            idempotency_key=f"k-{uuid.uuid4()}",
        ),
    )
    second = svc.get_or_generate(user, RecapPeriod.DAILY, LOCAL_DATE)
    assert provider.calls == 2  # regenerated once on next fetch


def test_empty_day_fallback_is_not_shaming(session, user):
    provider = FakeProvider(ProviderError(ProviderErrorKind.NO_KEY, "no key"))
    recap = RecapService(session, provider=provider).get_or_generate(
        user, RecapPeriod.DAILY, LOCAL_DATE
    )
    assert recap.status == GenerationStatus.FALLBACK
    lowered = recap.narrative.lower()
    for word in ("lazy", "wasted", "failed"):
        assert word not in lowered


# ---------------------------------------------------------------------------
# API-level tests (provider injected via dependency override)
# ---------------------------------------------------------------------------

@pytest.fixture()
def recap_client(session, media_root, monkeypatch):
    from app.core.config import get_settings
    from tests.conftest import TEST_PEPPER

    monkeypatch.setenv("AUTH_TOKEN_PEPPER", TEST_PEPPER)
    get_settings.cache_clear()
    app = create_app()

    def _override_session():
        yield session

    provider = GoodProvider()
    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[recaps_router.provider_override] = lambda: provider

    with TestClient(app) as c:
        c.provider = provider  # type: ignore[attr-defined]
        yield c


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_get_recaps_route(recap_client, session, authed):
    token, user = authed
    _seed_day_events(session, user)
    res = recap_client.get(
        f"/recaps?period=DAILY&date={LOCAL_DATE.isoformat()}",
        headers=_auth(token),
    )
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "GENERATED"
    assert body["period_start"] == LOCAL_DATE.isoformat()
    assert recap_client.provider.calls == 1


def test_recaps_require_auth(recap_client):
    assert recap_client.get("/recaps?period=DAILY").status_code == 401


def test_internal_run_daily(recap_client, session, authed):
    token, user = authed
    _seed_day_events(session, user)
    res = recap_client.post(
        f"/internal/run/daily?date={LOCAL_DATE.isoformat()}",
        headers=_auth(token),
    )
    assert res.status_code == 200
    assert res.json()["period_type"] == "DAILY"
    # Unknown jobs are honest 404s, not stubs.
    assert (
        recap_client.post("/internal/run/yearly", headers=_auth(token)).status_code
        == 404
    )


def test_monthly_yearly_not_generated(recap_client, authed):
    """MONTHLY/YEARLY remain contract-level only (post-V1). WEEKLY is
    generated since HWGA07 — covered in test_weekly_recap.py."""
    token, _user = authed
    for period in ("MONTHLY", "YEARLY"):
        res = recap_client.get(
            f"/recaps?period={period}", headers=_auth(token)
        )
        assert res.status_code == 404

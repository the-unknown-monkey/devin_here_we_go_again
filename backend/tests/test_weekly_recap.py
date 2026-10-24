"""HWGA07: weekly recap chain tests — mocked provider, real DB + graph.

Covers: stored DAILY recaps consumed via source_recap_ids (never raw
events), ISO week window, missing-day markers, partial current week,
provider failure -> FALLBACK, unsupported-claim rejection, idempotent
retry, staleness regeneration after a daily recap changes, and the
/recaps + /internal/run/weekly API contract.
"""

import uuid
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.routers import recaps as recaps_router
from app.agents.providers.gemini import ProviderError, ProviderErrorKind
from app.agents.schemas.receipt import CandidateInsight, RecapCandidate
from app.db.models import Event, RecapRow, User
from app.db.session import get_session
from app.domain.enums import (
    ConfirmationKind,
    EventType,
    GenerationStatus,
    RecapPeriod,
)
from app.main import create_app
from app.services.recaps import RecapService

# A fully elapsed ISO week (Mon Oct 5 – Sun Oct 11, 2026).
WEEK_MON = date(2026, 10, 5)
WEEK_SUN = date(2026, 10, 11)
DAY_A = date(2026, 10, 6)
DAY_B = date(2026, 10, 9)


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


def _daily(session, user, day, evidence_ids, narrative=None, media_ids=None):
    row = RecapRow(
        user_id=user.id,
        period_type=RecapPeriod.DAILY,
        period_start=day,
        period_end=day,
        narrative=narrative or f"A quiet day on {day.isoformat()}.",
        insights=[
            {
                "text": f"Logged moments on {day.isoformat()}.",
                "evidence_event_ids": [str(i) for i in evidence_ids],
            }
        ]
        if evidence_ids
        else [],
        highlight_media_ids=[str(i) for i in (media_ids or [])],
        directive_for_next_cycle=None,
        source_recap_ids=[],
        status=GenerationStatus.GENERATED,
        stale=False,
    )
    session.add(row)
    session.commit()
    return row


@pytest.fixture()
def two_daily_recaps(session, user):
    e1, e2, e3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    a = _daily(session, user, DAY_A, [e1, e2], narrative="You logged 2 waters.")
    b = _daily(session, user, DAY_B, [e3])
    return a, b, (e1, e2, e3)


class GoodWeeklyProvider:
    def __init__(self):
        self.calls = 0
        self.contexts = []

    def generate_weekly(self, context):
        self.calls += 1
        self.contexts.append(context)
        eid = str(context.evidence_event_ids[0]) if context.evidence_event_ids else "x"
        return RecapCandidate(
            narrative=f"A week with {context.days_covered} saved receipts.",
            insights=[
                CandidateInsight(text="Receipts kept the week visible.",
                                 evidence_event_ids=[eid])
            ] if context.evidence_event_ids else [],
            highlight_media_ids=[str(i) for i in context.highlight_media_ids[:3]],
        )


class FailingWeeklyProvider:
    def __init__(self, kind=ProviderErrorKind.TIMEOUT):
        self.calls = 0
        self._kind = kind

    def generate_weekly(self, context):
        self.calls += 1
        raise ProviderError(self._kind, "boom")


# ---------------------------------------------------------------------------
# Chain semantics
# ---------------------------------------------------------------------------

def test_weekly_consumes_stored_recaps_not_raw_events(
    session, user, two_daily_recaps
):
    a, b, evidence = two_daily_recaps
    # A raw event on a day with NO stored recap must not leak into the
    # weekly context — the chain consumes recaps, not event logs.
    session.add(
        Event(
            user_id=user.id,
            type=EventType.CONFIRMATION,
            kind=ConfirmationKind.WATER,
            occurred_at=datetime(2026, 10, 7, 6, 0, tzinfo=UTC),
            idempotency_key=f"k-{uuid.uuid4()}",
        )
    )
    session.commit()

    provider = GoodWeeklyProvider()
    recap = RecapService(session, provider=provider).get_or_generate(
        user, RecapPeriod.WEEKLY, DAY_B
    )
    assert recap.status == GenerationStatus.GENERATED
    assert recap.period_type == RecapPeriod.WEEKLY
    assert recap.period_start == WEEK_MON and recap.period_end == WEEK_SUN
    assert set(recap.source_recap_ids) == {a.id, b.id}

    ctx = provider.contexts[0]
    assert ctx.days_covered == 2
    assert {r.recap_id for r in ctx.daily_recaps} == {a.id, b.id}
    # Only evidence ids carried by the stored recaps are visible.
    assert set(ctx.evidence_event_ids) == set(evidence)


def test_missing_days_marked_deterministically(session, user, two_daily_recaps):
    provider = GoodWeeklyProvider()
    RecapService(session, provider=provider).get_or_generate(
        user, RecapPeriod.WEEKLY, WEEK_SUN
    )
    ctx = provider.contexts[0]
    # Fully elapsed week, 2 receipts stored -> 5 missing markers.
    assert ctx.missing_dates == [
        WEEK_MON,
        date(2026, 10, 7),
        date(2026, 10, 8),
        date(2026, 10, 10),
        WEEK_SUN,
    ]


def test_partial_current_week_marks_only_elapsed_days(session, user):
    """In the in-progress week, future days are not 'missing'."""
    today = datetime.now(UTC).astimezone().date()
    week_mon = today - timedelta(days=today.weekday())
    provider = GoodWeeklyProvider()
    recap = RecapService(session, provider=provider).get_or_generate(
        user, RecapPeriod.WEEKLY, today
    )
    assert recap.period_start == week_mon
    # No stored dailies this week: every elapsed day is a marker, future
    # days are simply not counted.
    ctx = provider.contexts[0]
    assert len(ctx.missing_dates) == (today - week_mon).days + 1
    assert all(d <= today for d in ctx.missing_dates)
    assert recap.status == GenerationStatus.GENERATED


def test_provider_failure_falls_back_with_coverage_facts(
    session, user, two_daily_recaps
):
    provider = FailingWeeklyProvider(ProviderErrorKind.QUOTA)
    recap = RecapService(session, provider=provider).get_or_generate(
        user, RecapPeriod.WEEKLY, DAY_B
    )
    assert recap.status == GenerationStatus.FALLBACK
    assert "2 days" in recap.narrative or "2 day" in recap.narrative
    assert set(recap.source_recap_ids) == {
        two_daily_recaps[0].id,
        two_daily_recaps[1].id,
    }
    lowered = recap.narrative.lower()
    for word in ("lazy", "failed", "missed"):
        assert word not in lowered


def test_unsupported_claims_rejected(session, user, two_daily_recaps):
    class BadProvider(GoodWeeklyProvider):
        def generate_weekly(self, context):
            self.calls += 1
            self.contexts.append(context)
            return RecapCandidate(
                narrative="You kept a perfect streak of 7 days.",
                insights=[
                    CandidateInsight(
                        text="Ghost evidence.",
                        evidence_event_ids=[str(uuid.uuid4())],
                    )
                ],
            )

    recap = RecapService(session, provider=BadProvider()).get_or_generate(
        user, RecapPeriod.WEEKLY, DAY_B
    )
    assert recap.status == GenerationStatus.FALLBACK
    assert "streak" not in recap.narrative.lower()


def test_idempotent_retry_does_not_regenerate(session, user, two_daily_recaps):
    provider = GoodWeeklyProvider()
    svc = RecapService(session, provider=provider)
    first = svc.get_or_generate(user, RecapPeriod.WEEKLY, DAY_B)
    second = svc.get_or_generate(user, RecapPeriod.WEEKLY, WEEK_SUN)
    assert first.id == second.id  # any date inside the week maps to it
    assert provider.calls == 1


def test_new_source_recap_marks_weekly_stale_and_regenerates(
    session, user, two_daily_recaps
):
    provider = GoodWeeklyProvider()
    svc = RecapService(session, provider=provider)
    first = svc.get_or_generate(user, RecapPeriod.WEEKLY, DAY_B)
    assert provider.calls == 1

    _daily(session, user, date(2026, 10, 8), [uuid.uuid4()])
    second = svc.get_or_generate(user, RecapPeriod.WEEKLY, DAY_B)
    assert provider.calls == 2
    assert second.id == first.id  # regenerated under the same period key
    assert len(second.source_recap_ids) == 3


def test_stale_daily_recap_regenerates_weekly(session, user, two_daily_recaps):
    a, _b, _ev = two_daily_recaps
    provider = GoodWeeklyProvider()
    svc = RecapService(session, provider=provider)
    svc.get_or_generate(user, RecapPeriod.WEEKLY, DAY_B)

    a.stale = True
    session.commit()
    svc.get_or_generate(user, RecapPeriod.WEEKLY, DAY_B)
    assert provider.calls == 2


def test_weekly_highlight_media_limited_to_source_refs(session, user):
    mid = uuid.uuid4()
    _daily(session, user, DAY_A, [uuid.uuid4()], media_ids=[mid])

    def build(context):
        return RecapCandidate(
            narrative="One saved receipt this week.",
            insights=[],
            highlight_media_ids=[str(mid), str(uuid.uuid4())],
        )

    class P(GoodWeeklyProvider):
        def generate_weekly(self, context):
            self.calls += 1
            self.contexts.append(context)
            return build(context)

    recap = RecapService(session, provider=P()).get_or_generate(
        user, RecapPeriod.WEEKLY, DAY_A
    )
    assert recap.highlight_media_ids == [mid]


# ---------------------------------------------------------------------------
# API-level tests
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

    provider = GoodWeeklyProvider()
    app.dependency_overrides[get_session] = _override_session
    app.dependency_overrides[recaps_router.provider_override] = lambda: provider

    with TestClient(app) as c:
        c.provider = provider  # type: ignore[attr-defined]
        yield c


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_weekly_recap_route(recap_client, session, authed):
    token, user = authed
    _daily(session, user, DAY_A, [uuid.uuid4()])
    res = recap_client.get(
        f"/recaps?period=WEEKLY&date={DAY_B.isoformat()}", headers=_auth(token)
    )
    assert res.status_code == 200
    body = res.json()
    assert body["period_type"] == "WEEKLY"
    assert body["period_start"] == WEEK_MON.isoformat()
    assert len(body["source_recap_ids"]) == 1


def test_internal_run_weekly(recap_client, session, authed):
    token, user = authed
    _daily(session, user, DAY_A, [uuid.uuid4()])
    res = recap_client.post(
        f"/internal/run/weekly?date={DAY_B.isoformat()}", headers=_auth(token)
    )
    assert res.status_code == 200
    assert res.json()["period_type"] == "WEEKLY"
    # Monthly/yearly jobs are still honest 404s.
    assert (
        recap_client.post("/internal/run/monthly", headers=_auth(token)).status_code
        == 404
    )

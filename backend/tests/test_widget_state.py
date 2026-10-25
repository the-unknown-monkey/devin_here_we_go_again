"""V2B: GET /widget/state tests — locked WidgetState contract.

Covers: bearer auth (401 unauth), empty-state defaults, logged-kinds-only
confirmations, quiet-moment count, current mode interval, goal count +
oldest age_days reuse, directive line sanitization/truncation, stored
receipt/directive statuses, missing receipt -> PENDING + stale=false, and
the side-effect-free rule (a fetch never generates a recap or directive).
"""

import uuid
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import func, select

from app.db.models import (
    AuthToken,
    Event,
    Goal,
    ModeIntervalRow,
    MorningDirectiveRow,
    RecapRow,
    User,
)
from app.domain.enums import (
    ConfirmationKind,
    EventType,
    GenerationStatus,
    GoalStatus,
    RecapPeriod,
    UserMode,
)
from tests.conftest import TEST_PEPPER

def _now() -> datetime:
    """Seed timestamps just inside the real current local-day window."""
    return datetime.now(UTC) - timedelta(minutes=1)


def _today(user: User) -> date:
    from zoneinfo import ZoneInfo

    return datetime.now(UTC).astimezone(ZoneInfo(user.timezone)).date()


@pytest.fixture()
def authed(session):
    from app.core.security import generate_token, hash_token

    u = User(timezone="Asia/Kolkata")
    session.add(u)
    session.flush()
    token = generate_token()
    session.add(AuthToken(user_id=u.id, token_hash=hash_token(token, TEST_PEPPER)))
    session.commit()
    return token, u


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _event(session, user, type_, kind=None, mode=None, occurred_at=None):
    e = Event(
        user_id=user.id,
        type=type_,
        kind=kind,
        mode=mode,
        occurred_at=occurred_at or _now(),
        idempotency_key=str(uuid.uuid4()),
    )
    session.add(e)
    session.commit()
    return e


def _stored_directive(session, user, content="Protect the morning.", status=GenerationStatus.GENERATED):
    row = MorningDirectiveRow(
        user_id=user.id, for_date=_today(user), content=content, status=status
    )
    session.add(row)
    session.commit()
    return row


def _stored_receipt(session, user, status=GenerationStatus.GENERATED, stale=False):
    row = RecapRow(
        user_id=user.id,
        period_type=RecapPeriod.DAILY,
        period_start=_today(user),
        period_end=_today(user),
        narrative="n",
        status=status,
        stale=stale,
    )
    session.add(row)
    session.commit()
    return row


def test_widget_state_requires_auth(client):
    res = client.get("/widget/state")
    assert res.status_code == 401
    assert res.json()["code"] == "UNAUTHORIZED"


def test_widget_state_empty_user(client, session, authed):
    token, _ = authed
    res = client.get("/widget/state", headers=_auth(token))
    assert res.status_code == 200
    body = res.json()
    assert body["generated_at"]
    assert body["mode"] is None
    assert body["today_confirmations"] == {}
    assert body["quiet_moments_today"] == 0
    assert body["goals_active"] == 0
    assert body["oldest_goal_age_days"] is None
    assert body["directive_line"] is None
    assert body["directive_status"] is None
    assert body["receipt_status"] == "PENDING"
    assert body["receipt_stale"] is False


def test_confirmations_logged_kinds_only(client, session, authed):
    token, user = authed
    for _ in range(3):
        _event(session, user, EventType.CONFIRMATION, kind=ConfirmationKind.WATER)
    _event(session, user, EventType.CONFIRMATION, kind=ConfirmationKind.STRETCH)
    _event(session, user, EventType.QUIET_MOMENT)
    # Yesterday's event must not leak into today's counts (IST day window).
    _event(
        session,
        user,
        EventType.CONFIRMATION,
        kind=ConfirmationKind.FOOD_CLEAN,
        occurred_at=_now() - timedelta(days=1),
    )

    body = client.get("/widget/state", headers=_auth(token)).json()
    assert body["today_confirmations"] == {"WATER": 3, "STRETCH": 1}
    assert "FOOD_CLEAN" not in body["today_confirmations"]
    assert body["quiet_moments_today"] == 1


def test_mode_and_goals(client, session, authed):
    token, user = authed
    started = _now() - timedelta(minutes=89)
    session.add(
        ModeIntervalRow(
            user_id=user.id, mode=UserMode.LOCKED_IN, started_at=started
        )
    )
    old = Goal(
        user_id=user.id,
        title="old",
        status=GoalStatus.ACTIVE,
        created_at=datetime.combine(
            _today(user) - timedelta(days=4),
            time(12, 0),
            tzinfo=ZoneInfo(user.timezone),
        ),
    )
    new = Goal(user_id=user.id, title="new", status=GoalStatus.ACTIVE)
    retired = Goal(
        user_id=user.id,
        title="done",
        status=GoalStatus.RETIRED,
        created_at=_now() - timedelta(days=30),
    )
    session.add_all([old, new, retired])
    session.commit()

    body = client.get("/widget/state", headers=_auth(token)).json()
    assert body["mode"]["mode"] == "LOCKED_IN"
    assert body["mode"]["ended_at"] is None
    assert body["mode"]["duration_min"] is not None
    assert body["goals_active"] == 2
    assert body["oldest_goal_age_days"] == 4


def test_directive_line_sanitized_and_truncated(client, session, authed):
    token, user = authed
    _stored_directive(
        session,
        user,
        content="First line.\nSecond line " + "x" * 200,
        status=GenerationStatus.FALLBACK,
    )
    body = client.get("/widget/state", headers=_auth(token)).json()
    assert body["directive_status"] == "FALLBACK"
    line = body["directive_line"]
    assert "\n" not in line
    assert len(line) <= 120
    assert line.startswith("First line. Second line")


def test_receipt_status_and_stale_passthrough(client, session, authed):
    token, user = authed
    _stored_receipt(session, user, status=GenerationStatus.FALLBACK, stale=True)
    _stored_directive(session, user)
    body = client.get("/widget/state", headers=_auth(token)).json()
    assert body["receipt_status"] == "FALLBACK"
    assert body["receipt_stale"] is True


def test_widget_state_is_side_effect_free(client, session, authed):
    """A fetch must never generate a recap or directive row."""
    token, user = authed
    before_recaps = session.scalar(select(func.count()).select_from(RecapRow))
    before_directives = session.scalar(
        select(func.count()).select_from(MorningDirectiveRow)
    )

    res = client.get("/widget/state", headers=_auth(token))
    assert res.status_code == 200

    assert session.scalar(select(func.count()).select_from(RecapRow)) == before_recaps
    assert (
        session.scalar(select(func.count()).select_from(MorningDirectiveRow))
        == before_directives
    )

"""HWGA06: deterministic DailyContext aggregation.

All facts (local-day window, counts, clipped mode durations, media refs,
idea transcripts, goal ages, evidence ids) are computed in code from the
user's IANA timezone — never by the model. Missing data is omitted, not
zeroed.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.db.models import Event, Goal, MediaAsset, ModeIntervalRow, User
from app.domain.enums import (
    ConfirmationKind,
    EventType,
    GoalStatus,
    MediaKind,
    TranscriptState,
    UserMode,
)
from app.services.daily_context import DailyContextService, local_day_window

TZ = ZoneInfo("Asia/Kolkata")  # UTC+5:30 — a non-hour offset, good boundary test
LOCAL_DATE = date(2026, 10, 20)
# Local day [00:00, 24:00) IST == [18:30, 18:30) UTC on Oct 19/20.
WINDOW_START = datetime(2026, 10, 19, 18, 30, tzinfo=UTC)
WINDOW_END = datetime(2026, 10, 20, 18, 30, tzinfo=UTC)


@pytest.fixture()
def user(session):
    u = User(timezone="Asia/Kolkata")
    session.add(u)
    session.commit()
    return u


def _event(user, type_, at, key=None, kind=None, mode=None):
    e = Event(
        user_id=user.id,
        type=type_,
        kind=kind,
        mode=mode,
        occurred_at=at,
        idempotency_key=key or f"k-{uuid.uuid4()}",
    )
    return e


def test_local_day_window_uses_user_timezone():
    start, end = local_day_window(TZ, LOCAL_DATE)
    assert start == WINDOW_START
    assert end == WINDOW_END
    assert end - start == timedelta(days=1)


def test_empty_day_is_honest(session, user):
    day = DailyContextService(session).build(user, LOCAL_DATE)
    ctx = day.context
    assert ctx.local_date == LOCAL_DATE
    assert ctx.timezone == "Asia/Kolkata"
    assert ctx.confirmations == {}  # missing = omitted, not zeroed
    assert ctx.quiet_moments == 0
    assert ctx.mode_intervals == []
    assert ctx.ideas == []
    assert ctx.media_asset_ids == []
    assert ctx.goals == []
    assert ctx.evidence_event_ids == []


def test_timezone_boundary_includes_only_local_day(session, user):
    inside_early = _event(
        user, EventType.CONFIRMATION, WINDOW_START, kind=ConfirmationKind.WATER
    )
    inside_late = _event(
        user,
        EventType.CONFIRMATION,
        WINDOW_END - timedelta(seconds=1),
        kind=ConfirmationKind.WATER,
    )
    just_before = _event(
        user,
        EventType.CONFIRMATION,
        WINDOW_START - timedelta(seconds=1),
        kind=ConfirmationKind.STRETCH,
    )
    just_after = _event(
        user,
        EventType.CONFIRMATION,
        WINDOW_END,
        kind=ConfirmationKind.STRETCH,
    )
    session.add_all([inside_early, inside_late, just_before, just_after])
    session.commit()

    ctx = DailyContextService(session).build(user, LOCAL_DATE).context
    assert ctx.confirmations == {"WATER": 2}  # STRETCH rows fell outside
    assert set(ctx.evidence_event_ids) == {inside_early.id, inside_late.id}


def test_confirmations_counted_only_when_logged(session, user):
    session.add_all(
        [
            _event(
                user, EventType.CONFIRMATION, WINDOW_START + timedelta(hours=1), kind=ConfirmationKind.WALK
            ),
            _event(
                user, EventType.CONFIRMATION, WINDOW_START + timedelta(hours=2), kind=ConfirmationKind.WALK
            ),
            _event(
                user, EventType.QUIET_MOMENT, WINDOW_START + timedelta(hours=3)
            ),
        ]
    )
    session.commit()
    ctx = DailyContextService(session).build(user, LOCAL_DATE).context
    assert ctx.confirmations == {"WALK": 2}
    assert "WATER" not in ctx.confirmations  # unknown, not zero
    assert ctx.quiet_moments == 1


def test_mode_intervals_clipped_to_window(session, user):
    # Spans midnight: started 22:00 local previous day, ended 02:00 local.
    # Only the 2 in-window hours may count.
    session.add(
        ModeIntervalRow(
            user_id=user.id,
            mode=UserMode.LOCKED_IN,
            started_at=WINDOW_START - timedelta(hours=2),
            ended_at=WINDOW_START + timedelta(hours=2),
        )
    )
    session.add(
        ModeIntervalRow(
            user_id=user.id,
            mode=UserMode.PURE_FUN_RECOVERY,
            started_at=WINDOW_START + timedelta(hours=5),
            ended_at=WINDOW_START + timedelta(hours=8),
        )
    )
    session.commit()
    ctx = DailyContextService(session).build(user, LOCAL_DATE).context
    by_mode = {iv.mode: iv for iv in ctx.mode_intervals}
    assert by_mode[UserMode.LOCKED_IN].duration_min == 120  # clipped, not 240
    assert by_mode[UserMode.LOCKED_IN].started_at == WINDOW_START
    assert by_mode[UserMode.PURE_FUN_RECOVERY].duration_min == 180


def test_media_refs_are_ids_and_ideas_need_transcript(session, user):
    img = MediaAsset(
        user_id=user.id,
        kind=MediaKind.IMAGE,
        captured_at=WINDOW_START + timedelta(hours=4),
        mime_type="image/jpeg",
        byte_length=10,
        storage_key=f"k/{uuid.uuid4()}",
        transcript_state=TranscriptState.NOT_APPLICABLE,
    )
    voice_with_text = MediaAsset(
        user_id=user.id,
        kind=MediaKind.VOICE,
        captured_at=WINDOW_START + timedelta(hours=5),
        mime_type="audio/mp4",
        byte_length=10,
        duration_sec=6.0,
        storage_key=f"k/{uuid.uuid4()}",
        transcript_state=TranscriptState.MANUAL_TEXT,
        transcript_text="idea: build the thing",
    )
    voice_pending = MediaAsset(
        user_id=user.id,
        kind=MediaKind.VOICE,
        captured_at=WINDOW_START + timedelta(hours=6),
        mime_type="audio/mp4",
        byte_length=10,
        duration_sec=4.0,
        storage_key=f"k/{uuid.uuid4()}",
        transcript_state=TranscriptState.PENDING,
    )
    session.add_all([img, voice_with_text, voice_pending])
    session.commit()

    ctx = DailyContextService(session).build(user, LOCAL_DATE).context
    assert set(ctx.media_asset_ids) == {img.id, voice_with_text.id, voice_pending.id}
    assert len(ctx.ideas) == 1
    assert ctx.ideas[0]["transcript_text"] == "idea: build the thing"
    # no storage_key or byte path anywhere in ideas
    assert "storage_key" not in ctx.ideas[0]


def test_goals_active_only_with_deterministic_age(session, user):
    active = Goal(
        user_id=user.id,
        title="Ship it",
        status=GoalStatus.ACTIVE,
        created_at=WINDOW_START - timedelta(days=4),
    )
    done = Goal(
        user_id=user.id,
        title="Old",
        status=GoalStatus.COMPLETED,
        created_at=WINDOW_START - timedelta(days=9),
        resolved_at=WINDOW_START - timedelta(days=1),
    )
    session.add_all([active, done])
    session.commit()
    ctx = DailyContextService(session).build(user, LOCAL_DATE).context
    assert [g.title for g in ctx.goals] == ["Ship it"]
    assert ctx.goals[0].status == GoalStatus.ACTIVE
    # age_days is computed at read from now(), just assert it is non-negative
    # and consistent between two reads.
    ctx2 = DailyContextService(session).build(user, LOCAL_DATE).context
    assert ctx.goals[0].age_days == ctx2.goals[0].age_days >= 0

"""HWGA04: POST /events ingestion + GET /timeline contract tests."""

import uuid
from datetime import UTC, datetime, timedelta

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _event(type_: str, key: str, **extra) -> dict:
    return {"type": type_, "idempotency_key": key, **extra}


def test_confirmation_event_accepted(client, issued_token):
    res = client.post(
        "/events",
        json=_event("CONFIRMATION", "k-water-1", kind="WATER"),
        headers=_auth(issued_token),
    )
    assert res.status_code == 201
    body = res.json()
    assert body["type"] == "CONFIRMATION"
    assert body["kind"] == "WATER"
    assert body["mode"] is None
    assert uuid.UUID(body["id"])
    datetime.fromisoformat(body["occurred_at"])


def test_confirmation_requires_kind(client, issued_token):
    res = client.post(
        "/events", json=_event("CONFIRMATION", "k-nokind"), headers=_auth(issued_token)
    )
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"


def test_quiet_moment_rejects_kind_and_mode(client, issued_token):
    res = client.post(
        "/events",
        json=_event("QUIET_MOMENT", "k-q1", kind="WATER"),
        headers=_auth(issued_token),
    )
    assert res.status_code == 422
    res = client.post(
        "/events",
        json=_event("QUIET_MOMENT", "k-q2", mode="LOCKED_IN"),
        headers=_auth(issued_token),
    )
    assert res.status_code == 422


def test_quiet_moment_accepted(client, issued_token):
    res = client.post(
        "/events", json=_event("QUIET_MOMENT", "k-q3"), headers=_auth(issued_token)
    )
    assert res.status_code == 201
    assert res.json()["type"] == "QUIET_MOMENT"


def test_media_captured_not_ingestible(client, issued_token):
    res = client.post(
        "/events", json=_event("MEDIA_CAPTURED", "k-m1"), headers=_auth(issued_token)
    )
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"


def test_occurred_at_is_honored(client, issued_token):
    at = (datetime.now(UTC) - timedelta(hours=3)).isoformat()
    res = client.post(
        "/events",
        json=_event("CONFIRMATION", "k-backfill", kind="WALK", occurred_at=at),
        headers=_auth(issued_token),
    )
    assert res.status_code == 201
    stored = datetime.fromisoformat(res.json()["occurred_at"])
    assert abs((stored - datetime.fromisoformat(at)).total_seconds()) < 1


def test_idempotent_replay_returns_same_event(client, issued_token):
    payload = _event("CONFIRMATION", "k-dup", kind="STRETCH")
    first = client.post("/events", json=payload, headers=_auth(issued_token))
    second = client.post("/events", json=payload, headers=_auth(issued_token))
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]

    timeline = client.get("/timeline", headers=_auth(issued_token)).json()
    dupes = [e for e in timeline["events"] if e["idempotency_key"] == "k-dup"]
    assert len(dupes) == 1


def test_events_require_auth(client):
    assert client.post("/events", json=_event("QUIET_MOMENT", "k-x")).status_code == 401
    assert client.get("/timeline").status_code == 401


def test_timeline_default_window_and_range_filter(client, issued_token):
    client.post(
        "/events",
        json=_event("CONFIRMATION", "k-tl-in", kind="FOOD_CLEAN"),
        headers=_auth(issued_token),
    )
    old = (datetime.now(UTC) - timedelta(days=10)).isoformat()
    client.post(
        "/events",
        json=_event("CONFIRMATION", "k-tl-old", kind="FOOD_CLEAN", occurred_at=old),
        headers=_auth(issued_token),
    )

    today = client.get("/timeline", headers=_auth(issued_token)).json()["events"]
    keys = {e["idempotency_key"] for e in today}
    assert "k-tl-in" in keys
    assert "k-tl-old" not in keys

    start = (datetime.now(UTC) - timedelta(days=11)).isoformat()
    end = (datetime.now(UTC) - timedelta(days=9)).isoformat()
    ranged = client.get(
        "/timeline",
        params={"from": start, "to": end},
        headers=_auth(issued_token),
    ).json()["events"]
    assert {e["idempotency_key"] for e in ranged} == {"k-tl-old"}

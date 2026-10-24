"""HWGA04: GET/POST /mode transition ordering + derived durations."""

from datetime import UTC, datetime, timedelta

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def test_mode_initially_empty(client, issued_token):
    res = client.get("/mode", headers=_auth(issued_token))
    assert res.status_code == 200
    assert res.json()["current"] is None


def test_first_transition_opens_interval(client, issued_token):
    res = client.post("/mode", json={"mode": "LOCKED_IN"}, headers=_auth(issued_token))
    assert res.status_code == 200
    body = res.json()
    assert body["event"]["type"] == "MODE_TRANSITION"
    assert body["event"]["mode"] == "LOCKED_IN"
    assert body["current"]["mode"] == "LOCKED_IN"
    assert body["current"]["ended_at"] is None
    assert body["current"]["duration_min"] >= 0


def test_same_mode_transition_rejected(client, issued_token):
    client.post("/mode", json={"mode": "LOCKED_IN"}, headers=_auth(issued_token))
    res = client.post("/mode", json={"mode": "LOCKED_IN"}, headers=_auth(issued_token))
    assert res.status_code == 422
    assert res.json()["code"] == "INVALID_MODE_TRANSITION"


def test_switch_closes_interval_and_derives_duration(client, issued_token):
    start = (datetime.now(UTC) - timedelta(minutes=45)).isoformat()
    client.post(
        "/mode",
        json={"mode": "LOCKED_IN", "occurred_at": start},
        headers=_auth(issued_token),
    )
    res = client.post(
        "/mode", json={"mode": "PURE_FUN_RECOVERY"}, headers=_auth(issued_token)
    )
    assert res.status_code == 200
    assert res.json()["current"]["mode"] == "PURE_FUN_RECOVERY"

    intervals = client.get("/mode", headers=_auth(issued_token)).json()["intervals"]
    closed = [i for i in intervals if i["ended_at"] is not None]
    assert len(closed) == 1
    assert closed[0]["mode"] == "LOCKED_IN"
    assert 44 <= closed[0]["duration_min"] <= 46


def test_transition_before_current_start_rejected(client, issued_token):
    client.post("/mode", json={"mode": "LOCKED_IN"}, headers=_auth(issued_token))
    past = (datetime.now(UTC) - timedelta(hours=1)).isoformat()
    res = client.post(
        "/mode",
        json={"mode": "PURE_FUN_RECOVERY", "occurred_at": past},
        headers=_auth(issued_token),
    )
    assert res.status_code == 422
    assert res.json()["code"] == "INVALID_MODE_TRANSITION"


def test_invalid_mode_value_rejected(client, issued_token):
    res = client.post("/mode", json={"mode": "GRIND"}, headers=_auth(issued_token))
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"


def test_mode_transition_idempotent_on_key(client, issued_token):
    payload = {"mode": "PURE_FUN_RECOVERY", "idempotency_key": "mode-key-1"}
    first = client.post("/mode", json=payload, headers=_auth(issued_token))
    assert first.status_code == 200
    second = client.post("/mode", json=payload, headers=_auth(issued_token))
    assert second.status_code == 200
    assert second.json()["event"]["id"] == first.json()["event"]["id"]

    # Idempotent replay must not have opened a second interval.
    events = client.get("/timeline", headers=_auth(issued_token)).json()["events"]
    mode_events = [e for e in events if e["idempotency_key"] == "mode-key-1"]
    assert len(mode_events) == 1


def test_mode_transition_via_events_route(client, issued_token):
    res = client.post(
        "/events",
        json={
            "type": "MODE_TRANSITION",
            "mode": "LOCKED_IN",
            "idempotency_key": "evt-mode-1",
        },
        headers=_auth(issued_token),
    )
    assert res.status_code == 201
    current = client.get("/mode", headers=_auth(issued_token)).json()["current"]
    assert current["mode"] == "LOCKED_IN"


def test_mode_requires_auth(client):
    assert client.get("/mode").status_code == 401
    assert client.post("/mode", json={"mode": "LOCKED_IN"}).status_code == 401

"""HWGA04: /goals Rule-of-3 lifecycle, D14 serialized enforcement, age_days."""

import threading
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import sessionmaker

from app.db.models import Goal, User
from app.domain.enums import GoalStatus
from app.services.goals import GoalService

def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _add(client, token, title):
    return client.post("/goals", json={"title": title}, headers=_auth(token))


def test_add_and_list_goals(client, issued_token):
    res = _add(client, issued_token, "Ship the thing")
    assert res.status_code == 201
    body = res.json()
    assert body["title"] == "Ship the thing"
    assert body["status"] == "ACTIVE"
    assert body["resolved_at"] is None
    assert body["age_days"] == 0

    listed = client.get("/goals", headers=_auth(issued_token)).json()
    assert any(g["id"] == body["id"] for g in listed)


def test_fourth_active_goal_rejected_with_cap(client, issued_token):
    for i in range(3):
        assert _add(client, issued_token, f"goal {i}").status_code == 201
    res = _add(client, issued_token, "one too many")
    assert res.status_code == 409
    body = res.json()
    assert body["code"] == "GOAL_CAP_REACHED"
    assert body["details"]["active_goals"] == 3


def test_complete_frees_slot(client, issued_token):
    ids = [_add(client, issued_token, f"g{i}").json()["id"] for i in range(3)]
    res = client.post(f"/goals/{ids[0]}/complete", headers=_auth(issued_token))
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"
    assert res.json()["resolved_at"] is not None
    assert _add(client, issued_token, "replacement").status_code == 201


def test_retire_frees_slot(client, issued_token):
    ids = [_add(client, issued_token, f"g{i}").json()["id"] for i in range(3)]
    res = client.post(f"/goals/{ids[1]}/retire", headers=_auth(issued_token))
    assert res.status_code == 200
    assert res.json()["status"] == "RETIRED"
    assert _add(client, issued_token, "replacement").status_code == 201


def test_resolving_missing_or_resolved_goal_404(client, issued_token):
    fake = "00000000-0000-0000-0000-000000000000"
    assert client.post(f"/goals/{fake}/complete", headers=_auth(issued_token)).status_code == 404

    gid = _add(client, issued_token, "once").json()["id"]
    assert client.post(f"/goals/{gid}/retire", headers=_auth(issued_token)).status_code == 200
    second = client.post(f"/goals/{gid}/complete", headers=_auth(issued_token))
    assert second.status_code == 404
    assert second.json()["code"] == "NOT_FOUND"


def test_empty_title_rejected(client, issued_token):
    assert _add(client, issued_token, "").status_code == 422
    assert _add(client, issued_token, "   ").status_code == 422
    assert _add(client, issued_token, "x" * 501).status_code == 422


def test_age_days_computed_from_timezone(client, session, issued_token):
    user_id = uuid.UUID(client.get("/me", headers=_auth(issued_token)).json()["user_id"])
    user = session.get(User, user_id)
    goal = Goal(
        user_id=user.id,
        title="old goal",
        status=GoalStatus.ACTIVE,
        created_at=datetime.now(UTC) - timedelta(days=5),
    )
    session.add(goal)
    session.commit()
    listed = client.get("/goals", headers=_auth(issued_token)).json()
    match = [g for g in listed if g["title"] == "old goal"]
    assert match and match[0]["age_days"] in (4, 5, 6)  # tz boundary tolerant


def test_goals_require_auth(client):
    assert client.get("/goals").status_code == 401
    assert client.post("/goals", json={"title": "x"}).status_code == 401


def test_concurrent_add_never_exceeds_cap(test_engine, session):
    """D14: serialized per-user lock — racing adds at the cap boundary
    resolve to exactly one success and 409 for the loser."""
    user = User(timezone="Asia/Kolkata")
    session.add(user)
    session.commit()
    uid = user.id
    for i in range(2):
        session.add(Goal(user_id=uid, title=f"seed {i}", status=GoalStatus.ACTIVE))
    session.commit()

    factory = sessionmaker(bind=test_engine, expire_on_commit=False)
    results = []

    def attempt(title):
        with factory() as s:
            u = s.get(User, uid)
            try:
                GoalService(s).add(u, title)
                results.append("ok")
            except Exception as exc:  # DomainError GOAL_CAP_REACHED
                s.rollback()
                results.append(getattr(exc, "code", type(exc).__name__))

    threads = [
        threading.Thread(target=attempt, args=("concurrent-a",)),
        threading.Thread(target=attempt, args=("concurrent-b",)),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)

    assert sorted(results) == ["GOAL_CAP_REACHED", "ok"]

    with factory() as s:
        from app.db.repositories.goals import GoalRepository
        assert GoalRepository(s).count_active(uid) == 3

def test_missing_credentials_rejected(client):
    resp = client.get("/_probe")
    assert resp.status_code == 401
    assert resp.json()["code"] == "UNAUTHORIZED"


def test_wrong_token_rejected(client):
    resp = client.get("/_probe", headers={"Authorization": "Bearer definitely-wrong"})
    assert resp.status_code == 401


def test_non_bearer_scheme_rejected(client, issued_token):
    resp = client.get("/_probe", headers={"Authorization": f"Basic {issued_token}"})
    assert resp.status_code == 401


def test_issued_token_accepted(client, issued_token):
    resp = client.get("/_probe", headers={"Authorization": f"Bearer {issued_token}"})
    assert resp.status_code == 200


def test_me_requires_auth(client):
    assert client.get("/me").status_code == 401


def test_me_returns_profile(client, issued_token):
    resp = client.get("/me", headers={"Authorization": f"Bearer {issued_token}"})
    assert resp.status_code == 200
    body = resp.json()
    assert "user_id" in body
    assert body["timezone"] == "Asia/Kolkata"

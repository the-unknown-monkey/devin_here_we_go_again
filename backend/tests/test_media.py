"""HWGA05 media lifecycle tests: auth, ownership, MIME/size/duration
validation (D18), metadata privacy, and delete cleanup."""

import uuid

import pytest

from app.core.security import generate_token, hash_token
from app.db.models import AuthToken, User
from tests.conftest import TEST_PEPPER

JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
M4A = b"\x00\x00\x00\x18ftypM4A " + b"\x00" * 64
WAV = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 64
NOT_MEDIA = b"this is plain text, not a media file"


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _upload(client, token, data, content_type, fields=None):
    return client.post(
        "/media",
        headers=_auth(token),
        files={"file": ("capture.bin", data, content_type)},
        data=fields or {},
    )


def test_upload_requires_auth(client):
    res = _upload(client, "no-such-token", JPEG, "image/jpeg")
    assert res.status_code == 401
    assert res.json()["code"] == "UNAUTHORIZED"


def test_media_routes_require_auth(client):
    assert client.get(f"/media/{uuid.uuid4()}").status_code == 401
    assert client.delete(f"/media/{uuid.uuid4()}").status_code == 401


def test_image_round_trip_and_delete_cleanup(client, issued_token, media_root):
    res = _upload(client, issued_token, JPEG, "image/jpeg")
    assert res.status_code == 201, res.text
    meta = res.json()
    assert meta["kind"] == "IMAGE"
    assert meta["mime_type"] == "image/jpeg"
    assert meta["byte_length"] == len(JPEG)
    assert meta["transcript_state"] == "NOT_APPLICABLE"
    # Opaque storage key / filesystem path must never be exposed.
    assert "storage_key" not in meta
    assert all("media" not in str(v) or ":\\" not in str(v) for v in meta.values())

    files = list(media_root.rglob("*.*"))
    assert len(files) == 1

    got = client.get(f"/media/{meta['id']}", headers=_auth(issued_token))
    assert got.status_code == 200
    assert got.content == JPEG
    assert got.headers["content-type"].startswith("image/jpeg")

    deleted = client.delete(f"/media/{meta['id']}", headers=_auth(issued_token))
    assert deleted.status_code == 204
    assert list(media_root.rglob("*.*")) == []
    assert (
        client.get(f"/media/{meta['id']}", headers=_auth(issued_token)).status_code
        == 404
    )


def test_malformed_mime_rejected(client, issued_token):
    res = _upload(client, issued_token, NOT_MEDIA, "image/jpeg")
    assert res.status_code == 422
    assert res.json()["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_disallowed_mime_rejected(client, issued_token):
    # Valid GIF magic bytes, but GIF is not on the D18 allowlist.
    gif = b"GIF89a" + b"\x00" * 64
    res = _upload(client, issued_token, gif, "image/gif")
    assert res.status_code == 422
    assert res.json()["code"] == "UNSUPPORTED_MEDIA_TYPE"


def test_oversize_image_rejected(client, issued_token):
    big = JPEG + b"\x00" * (10 * 1024 * 1024)
    res = _upload(client, issued_token, big, "image/jpeg")
    assert res.status_code == 413
    assert res.json()["code"] == "MEDIA_LIMIT_EXCEEDED"


def test_over_duration_audio_rejected(client, issued_token):
    res = _upload(
        client,
        issued_token,
        M4A,
        "audio/mp4",
        fields={"kind": "AUDIO", "duration_sec": "61"},
    )
    assert res.status_code == 413
    assert res.json()["code"] == "MEDIA_LIMIT_EXCEEDED"


def test_audio_upload_ok(client, issued_token):
    res = _upload(
        client,
        issued_token,
        WAV,
        "audio/wav",
        fields={"kind": "AUDIO", "duration_sec": "8.5"},
    )
    assert res.status_code == 201, res.text
    meta = res.json()
    assert meta["kind"] == "AUDIO"
    assert meta["duration_sec"] == 8.5


def test_invalid_kind_rejected(client, issued_token):
    res = _upload(client, issued_token, JPEG, "image/jpeg", fields={"kind": "VIDEO"})
    assert res.status_code == 422


def test_image_with_duration_rejected(client, issued_token):
    res = _upload(
        client, issued_token, JPEG, "image/jpeg", fields={"duration_sec": "5"}
    )
    assert res.status_code == 422
    assert res.json()["code"] == "VALIDATION_ERROR"


def test_voice_transcript_states(client, issued_token):
    pending = _upload(
        client, issued_token, M4A, "audio/mp4", fields={"kind": "VOICE", "duration_sec": "4"}
    )
    assert pending.status_code == 201, pending.text
    assert pending.json()["transcript_state"] == "PENDING"

    manual = _upload(
        client,
        issued_token,
        M4A,
        "audio/mp4",
        fields={
            "kind": "VOICE",
            "duration_sec": "4",
            "transcript_text": "2am idea: build the thing",
        },
    )
    assert manual.status_code == 201, manual.text
    body = manual.json()
    assert body["transcript_state"] == "MANUAL_TEXT"
    assert body["transcript_text"] == "2am idea: build the thing"


def test_transcript_rejected_for_non_voice(client, issued_token):
    res = _upload(
        client,
        issued_token,
        JPEG,
        "image/jpeg",
        fields={"transcript_text": "nope"},
    )
    assert res.status_code == 422


def test_foreign_owner_cannot_read_or_delete(client, session, issued_token):
    res = _upload(client, issued_token, PNG, "image/png")
    assert res.status_code == 201, res.text
    asset_id = res.json()["id"]

    other = User(timezone="Asia/Kolkata")
    session.add(other)
    session.flush()
    foreign_token = generate_token()
    session.add(
        AuthToken(user_id=other.id, token_hash=hash_token(foreign_token, TEST_PEPPER))
    )
    session.commit()

    # No existence leak: foreign access looks like a plain 404.
    assert (
        client.get(f"/media/{asset_id}", headers=_auth(foreign_token)).status_code
        == 404
    )
    assert (
        client.delete(
            f"/media/{asset_id}", headers=_auth(foreign_token)
        ).status_code
        == 404
    )
    # Owner can still read it.
    assert (
        client.get(f"/media/{asset_id}", headers=_auth(issued_token)).status_code
        == 200
    )


def test_unknown_id_is_404(client, issued_token):
    assert (
        client.get(f"/media/{uuid.uuid4()}", headers=_auth(issued_token)).status_code
        == 404
    )


def test_timeline_includes_media_refs(client, issued_token):
    res = _upload(client, issued_token, JPEG, "image/jpeg")
    assert res.status_code == 201
    asset_id = res.json()["id"]

    timeline = client.get("/timeline", headers=_auth(issued_token))
    assert timeline.status_code == 200
    body = timeline.json()
    ids = [m["id"] for m in body["media"]]
    assert asset_id in ids
    assert all("storage_key" not in m for m in body["media"])
    assert any(e["type"] == "MEDIA_CAPTURED" for e in body["events"])

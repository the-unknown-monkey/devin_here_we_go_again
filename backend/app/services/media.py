"""Sensory Moment Vault — private media lifecycle (contracts.md §2/§3/§4).

Bytes live on backend-controlled local disk via LocalMediaStorage; only
metadata lands in Postgres. `storage_key` is opaque and NEVER serialized to
clients. VOICE transcript rules (D19): user-supplied text lands as
MANUAL_TEXT; without it the clip stays PENDING for the approved server-side
Gemini STT step (wired in the agent phases — no raw media leaves this box
here). IMAGE/AUDIO transcripts are NOT_APPLICABLE.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from app.db.models import Event, MediaAsset, User
from app.db.repositories.events import EventRepository
from app.db.repositories.media import MediaAssetRepository
from app.domain import errors
from app.domain.enums import EventType, MediaKind, TranscriptState
from app.storage.local import (
    LocalMediaStorage,
    MediaLimitExceeded,
    StorageError,
    StorageKeyNotFound,
    UnsupportedMediaType,
)


def serialize_media(asset: MediaAsset) -> dict:
    """MediaAssetMeta — storage_key deliberately omitted."""
    return {
        "id": str(asset.id),
        "kind": asset.kind.value,
        "captured_at": asset.captured_at.isoformat(),
        "mime_type": asset.mime_type,
        "byte_length": asset.byte_length,
        "duration_sec": asset.duration_sec,
        "transcript_state": asset.transcript_state.value,
        "transcript_text": asset.transcript_text,
    }


def _to_domain(exc: StorageError) -> errors.DomainError:
    status = {"MEDIA_LIMIT_EXCEEDED": 413, "UNSUPPORTED_MEDIA_TYPE": 422, "NOT_FOUND": 404}
    return errors.DomainError(exc.code, str(exc), status.get(exc.code, 500))


class MediaService:
    def __init__(self, session: Session, storage: LocalMediaStorage):
        self.session = session
        self.storage = storage
        self.media = MediaAssetRepository(session)
        self.events = EventRepository(session)

    def upload(
        self,
        user: User,
        *,
        kind: MediaKind,
        mime_type: str,
        data: bytes,
        duration_sec: float | None = None,
        captured_at: datetime | None = None,
        transcript_text: str | None = None,
    ) -> MediaAsset:
        if kind == MediaKind.IMAGE and duration_sec is not None:
            raise errors.validation("duration_sec is only valid for AUDIO/VOICE media")
        if kind != MediaKind.VOICE and transcript_text is not None:
            raise errors.validation("transcript_text is only valid for VOICE media")
        if duration_sec is not None and duration_sec <= 0:
            raise errors.validation("duration_sec must be positive")
        if captured_at is not None and captured_at.tzinfo is None:
            captured_at = captured_at.replace(tzinfo=UTC)
        transcript = transcript_text.strip() if transcript_text else None
        if transcript_text is not None and not transcript:
            raise errors.validation("transcript_text must be non-empty when provided")

        try:
            storage_key, byte_length = self.storage.save(
                kind, mime_type, data, duration_sec
            )
        except StorageError as exc:
            raise _to_domain(exc) from exc

        if kind == MediaKind.VOICE:
            transcript_state = (
                TranscriptState.MANUAL_TEXT if transcript else TranscriptState.PENDING
            )
        else:
            transcript_state = TranscriptState.NOT_APPLICABLE
            transcript = None

        asset = MediaAsset(
            user_id=user.id,
            kind=kind,
            captured_at=captured_at or datetime.now(UTC),
            mime_type=mime_type,
            byte_length=byte_length,
            duration_sec=duration_sec,
            storage_key=storage_key,
            transcript_state=transcript_state,
            transcript_text=transcript,
        )
        try:
            self.media.add(asset)
            self.events.add(
                Event(
                    user_id=user.id,
                    type=EventType.MEDIA_CAPTURED,
                    occurred_at=asset.captured_at,
                    idempotency_key=f"media:{asset.id}",
                )
            )
            from app.services.recaps import RecapService

            RecapService(self.session).mark_stale_for_local_date(user, asset.captured_at)
            self.session.commit()
        except Exception:
            # Never leave orphaned bytes when the metadata row fails.
            self.session.rollback()
            self.storage.delete(storage_key)
            raise
        return asset

    def get_owned(self, user: User, asset_id: uuid.UUID) -> MediaAsset:
        """Owner check with no existence leak: foreign ids look like 404."""
        asset = self.media.get(asset_id)
        if asset is None or asset.user_id != user.id:
            raise errors.not_found("Media not found")
        return asset

    def read_bytes(self, user: User, asset_id: uuid.UUID) -> tuple[MediaAsset, bytes]:
        asset = self.get_owned(user, asset_id)
        try:
            return asset, self.storage.open(asset.storage_key)
        except StorageKeyNotFound as exc:
            raise _to_domain(exc) from exc

    def delete(self, user: User, asset_id: uuid.UUID) -> None:
        asset = self.get_owned(user, asset_id)
        storage_key = asset.storage_key
        self.session.delete(asset)
        self.session.commit()
        self.storage.delete(storage_key)

    def timeline_media(
        self, user: User, start: datetime, end: datetime
    ) -> list[MediaAsset]:
        return self.media.list_for_user_between(user.id, start, end)

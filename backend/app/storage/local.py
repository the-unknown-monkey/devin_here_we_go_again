"""Local-disk media storage adapter scaffold.

Owns safe file naming, path confinement, size/duration/MIME limits (D18),
and stream reads/deletes. No FastAPI static mount anywhere; media is served
only via the authenticated /media/{id} route added in HWGA05.
"""

import uuid
from dataclasses import dataclass
from pathlib import Path

from app.domain.enums import MediaKind


class StorageError(Exception):
    code = "STORAGE_ERROR"


class MediaLimitExceeded(StorageError):
    code = "MEDIA_LIMIT_EXCEEDED"  # -> 413


class UnsupportedMediaType(StorageError):
    code = "UNSUPPORTED_MEDIA_TYPE"  # -> 422


class StorageKeyNotFound(StorageError):
    code = "NOT_FOUND"  # -> 404


@dataclass(frozen=True)
class MediaRule:
    max_bytes: int
    mime_types: frozenset[str]
    max_duration_sec: float | None


MEDIA_RULES: dict[MediaKind, MediaRule] = {
    MediaKind.IMAGE: MediaRule(
        max_bytes=10 * 1024 * 1024,
        mime_types=frozenset({"image/jpeg", "image/png", "image/webp"}),
        max_duration_sec=None,
    ),
    MediaKind.AUDIO: MediaRule(
        max_bytes=15 * 1024 * 1024,
        mime_types=frozenset({"audio/mp4", "audio/aac", "audio/mpeg", "audio/wav"}),
        max_duration_sec=60,
    ),
    MediaKind.VOICE: MediaRule(
        max_bytes=15 * 1024 * 1024,
        mime_types=frozenset({"audio/mp4", "audio/aac", "audio/mpeg", "audio/wav"}),
        max_duration_sec=60,
    ),
}

_EXT_BY_MIME = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "audio/mp4": ".m4a",
    "audio/aac": ".aac",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
}


class LocalMediaStorage:
    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def validate(
        self, kind: MediaKind, mime_type: str, byte_length: int, duration_sec: float | None
    ) -> None:
        rule = MEDIA_RULES[kind]
        if mime_type not in rule.mime_types:
            raise UnsupportedMediaType(f"MIME {mime_type!r} not allowed for {kind.value}")
        if byte_length > rule.max_bytes:
            raise MediaLimitExceeded(f"{kind.value} exceeds {rule.max_bytes} bytes")
        if (
            rule.max_duration_sec is not None
            and duration_sec is not None
            and duration_sec > rule.max_duration_sec
        ):
            raise MediaLimitExceeded(
                f"{kind.value} exceeds {rule.max_duration_sec}s duration"
            )

    def new_storage_key(self, kind: MediaKind, mime_type: str) -> str:
        """Server-generated opaque key; never derived from client filenames."""
        ext = _EXT_BY_MIME.get(mime_type, "")
        return f"{kind.value.lower()}/{uuid.uuid4()}{ext}"

    def _resolve(self, storage_key: str) -> Path:
        path = (self.root / storage_key).resolve()
        if self.root not in path.parents:
            raise StorageError("storage key escapes media root")
        return path

    def save(
        self,
        kind: MediaKind,
        mime_type: str,
        data: bytes,
        duration_sec: float | None = None,
    ) -> tuple[str, int]:
        """Validate + write bytes; returns (storage_key, byte_length)."""
        self.validate(kind, mime_type, len(data), duration_sec)
        key = self.new_storage_key(kind, mime_type)
        path = self._resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return key, len(data)

    def open(self, storage_key: str) -> bytes:
        path = self._resolve(storage_key)
        if not path.is_file():
            raise StorageKeyNotFound(storage_key)
        return path.read_bytes()

    def delete(self, storage_key: str) -> None:
        path = self._resolve(storage_key)
        if path.is_file():
            path.unlink()

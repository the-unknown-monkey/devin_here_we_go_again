"""/media — authenticated private media round trip (contracts.md §3).

POST /media: multipart upload. The client sends bytes + declared properties;
every property is re-validated server-side (kind, MIME allowlist + magic
bytes, D18 size/duration caps). The returned MediaAssetMeta never contains
storage_key or any filesystem path.

GET/DELETE /media/{id}: owner-only; foreign ids return 404 so existence
never leaks. No static mount exists anywhere.
"""

import uuid
from datetime import datetime
from functools import lru_cache

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.security import require_auth
from app.db.models import User
from app.db.session import get_session
from app.domain.enums import MediaKind
from app.domain.errors import DomainError
from app.services.media import MediaService, serialize_media
from app.storage.local import LocalMediaStorage

router = APIRouter()

# Largest accepted upload is 15 MB (D18) — read one byte past it to detect
# overflow without buffering unbounded bodies.
_MAX_UPLOAD_READ = 15 * 1024 * 1024 + 1


@lru_cache
def _cached_storage(root: str) -> LocalMediaStorage:
    return LocalMediaStorage(root)


def get_storage(settings: Settings = Depends(get_settings)) -> LocalMediaStorage:
    return _cached_storage(str(settings.media_storage_root.resolve()))


@router.post("/media", status_code=201)
async def upload_media(
    file: UploadFile = File(...),
    kind: str | None = Form(default=None),
    duration_sec: float | None = Form(default=None),
    captured_at: datetime | None = Form(default=None),
    transcript_text: str | None = Form(default=None),
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
    storage: LocalMediaStorage = Depends(get_storage),
):
    data = await file.read(_MAX_UPLOAD_READ)
    # Client-declared content type is a hint only; the service validates it
    # against the allowlist AND the actual bytes.
    declared_mime = (file.content_type or "").split(";")[0].strip().lower()
    if kind is None:
        # VOICE is always explicit; an omitted kind means IMAGE or AUDIO.
        media_kind = (
            MediaKind.IMAGE if declared_mime.startswith("image/") else MediaKind.AUDIO
        )
    else:
        try:
            media_kind = MediaKind(kind)
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "VALIDATION_ERROR",
                    "message": f"kind must be one of {[k.value for k in MediaKind]}",
                    "details": {},
                },
            ) from None
    try:
        asset = MediaService(session, storage).upload(
            user,
            kind=media_kind,
            mime_type=declared_mime,
            data=data,
            duration_sec=duration_sec,
            captured_at=captured_at,
            transcript_text=transcript_text,
        )
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.payload()) from exc
    return serialize_media(asset)


@router.get("/media/{asset_id}")
def get_media(
    asset_id: uuid.UUID,
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
    storage: LocalMediaStorage = Depends(get_storage),
):
    try:
        asset, data = MediaService(session, storage).read_bytes(user, asset_id)
    except DomainError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.payload()) from exc
    return Response(
        content=data,
        media_type=asset.mime_type,
        headers={
            "Content-Length": str(len(data)),
            # Opaque download name — never a storage path or client filename.
            "Content-Disposition": f'inline; filename="{asset.id}"',
            "Cache-Control": "private, no-store",
        },
    )


@router.delete("/media/{asset_id}", status_code=204)
def delete_media(
    asset_id: uuid.UUID,
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
    storage: LocalMediaStorage = Depends(get_storage),
):
    try:
        MediaService(session, storage).delete(user, asset_id)
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.payload()) from exc
    return Response(status_code=204)

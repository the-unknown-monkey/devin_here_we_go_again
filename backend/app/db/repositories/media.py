import uuid
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MediaAsset


class MediaAssetRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, asset_id: uuid.UUID) -> MediaAsset | None:
        return self.session.get(MediaAsset, asset_id)

    def add(self, asset: MediaAsset) -> MediaAsset:
        self.session.add(asset)
        self.session.flush()
        return asset

    def list_for_user(self, user_id: uuid.UUID) -> list[MediaAsset]:
        return list(
            self.session.execute(
                select(MediaAsset)
                .where(MediaAsset.user_id == user_id)
                .order_by(MediaAsset.captured_at)
            ).scalars()
        )

    def list_for_user_between(
        self, user_id: uuid.UUID, start: datetime, end: datetime
    ) -> list[MediaAsset]:
        return list(
            self.session.execute(
                select(MediaAsset)
                .where(
                    MediaAsset.user_id == user_id,
                    MediaAsset.captured_at >= start,
                    MediaAsset.captured_at < end,
                )
                .order_by(MediaAsset.captured_at)
            ).scalars()
        )

    def delete(self, asset: MediaAsset) -> None:
        self.session.delete(asset)

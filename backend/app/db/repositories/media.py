import uuid

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

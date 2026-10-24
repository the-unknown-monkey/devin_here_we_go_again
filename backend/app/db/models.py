"""SQLAlchemy ORM models mirroring docs/hwga/contracts.md §2.

Enum columns use native_enum=False (varchar + CHECK) so values stay the
locked contract spellings without DB-side enum migrations.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    JSON,
    func,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.domain.enums import (
    ConfirmationKind,
    EventType,
    GenerationStatus,
    GoalStatus,
    MediaKind,
    RecapPeriod,
    TranscriptState,
    UserMode,
)


def _enum(e: type) -> Enum:
    return Enum(e, native_enum=False, validate_strings=True)


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Kolkata")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    tokens: Mapped[list["AuthToken"]] = relationship(back_populates="user")


class AuthToken(Base):
    """Bootstrap-CLI-issued bearer token, stored hashed (HMAC-SHA256 + pepper).
    The plaintext token is shown once by the CLI and never persisted (D07)."""

    __tablename__ = "auth_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="tokens")


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_events_user_idem"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[EventType] = mapped_column(_enum(EventType), nullable=False)
    kind: Mapped[ConfirmationKind | None] = mapped_column(_enum(ConfirmationKind))
    mode: Mapped[UserMode | None] = mapped_column(_enum(UserMode))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ModeIntervalRow(Base):
    __tablename__ = "mode_intervals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    mode: Mapped[UserMode] = mapped_column(_enum(UserMode), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[GoalStatus] = mapped_column(_enum(GoalStatus), default=GoalStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MediaAsset(Base):
    """Metadata only. `storage_key` is an opaque backend-owned relative key —
    never returned to clients, never a client-supplied path."""

    __tablename__ = "media_assets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    kind: Mapped[MediaKind] = mapped_column(_enum(MediaKind), nullable=False)
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    byte_length: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_sec: Mapped[float | None] = mapped_column(Float)
    storage_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    transcript_state: Mapped[TranscriptState] = mapped_column(
        _enum(TranscriptState), default=TranscriptState.NOT_APPLICABLE
    )
    transcript_text: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecapRow(Base):
    __tablename__ = "recaps"
    __table_args__ = (
        UniqueConstraint("user_id", "period_type", "period_start", name="uq_recaps_period"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    period_type: Mapped[RecapPeriod] = mapped_column(_enum(RecapPeriod), nullable=False)
    period_start: Mapped[date] = mapped_column(Date, nullable=False)
    period_end: Mapped[date] = mapped_column(Date, nullable=False)
    narrative: Mapped[str] = mapped_column(Text, nullable=False, default="")
    insights: Mapped[list] = mapped_column(JSON, default=list)
    highlight_media_ids: Mapped[list] = mapped_column(JSON, default=list)
    directive_for_next_cycle: Mapped[str | None] = mapped_column(Text)
    source_recap_ids: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[GenerationStatus] = mapped_column(
        _enum(GenerationStatus), default=GenerationStatus.PENDING
    )
    stale: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MorningDirectiveRow(Base):
    __tablename__ = "morning_directives"
    __table_args__ = (
        UniqueConstraint("user_id", "for_date", name="uq_directives_user_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    for_date: Mapped[date] = mapped_column(Date, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_recap_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("recaps.id", ondelete="SET NULL")
    )
    status: Mapped[GenerationStatus] = mapped_column(
        _enum(GenerationStatus), default=GenerationStatus.PENDING
    )
    shown_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

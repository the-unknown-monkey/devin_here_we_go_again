"""Canonical enums — verbatim from docs/hwga/contracts.md §1 (LOCKED HWGA01)."""

from enum import Enum


class UserMode(str, Enum):
    LOCKED_IN = "LOCKED_IN"
    PURE_FUN_RECOVERY = "PURE_FUN_RECOVERY"


class GoalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    RETIRED = "RETIRED"


class EventType(str, Enum):
    CONFIRMATION = "CONFIRMATION"
    MODE_TRANSITION = "MODE_TRANSITION"
    QUIET_MOMENT = "QUIET_MOMENT"
    MEDIA_CAPTURED = "MEDIA_CAPTURED"


class ConfirmationKind(str, Enum):
    WATER = "WATER"
    FOOD_CLEAN = "FOOD_CLEAN"
    STRETCH = "STRETCH"
    POSTURE_RESET = "POSTURE_RESET"
    WALK = "WALK"


class MediaKind(str, Enum):
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    VOICE = "VOICE"


class TranscriptState(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    MANUAL_TEXT = "MANUAL_TEXT"
    FAILED = "FAILED"


class RecapPeriod(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class GenerationStatus(str, Enum):
    PENDING = "PENDING"
    GENERATED = "GENERATED"
    FALLBACK = "FALLBACK"
    FAILED = "FAILED"

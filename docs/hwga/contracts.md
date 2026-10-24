# HWGA Contracts — Single Source of Truth

- **Document ID:** CONTRACTS-HWGA
- **Project:** Here We Go Again (HWGA)
- **Status:** **LOCKED (HWGA01, 2026-10-25)** — frozen for V1; changes require explicit user approval recorded in `status.md`
- **Authority:** This file is the ONLY authoritative definition of enums, typed models, API shapes, and error formats. `here_we_go_again.md` §7–8 and any JSON examples elsewhere are illustrative drafts; if they disagree with this file, this file wins and the other doc must be corrected.

---

## 1. Canonical Enums

Use these exact spellings everywhere: code, database values, API payloads, docs.

```python
from enum import Enum

class UserMode(str, Enum):
    LOCKED_IN = "LOCKED_IN"                    # 100% focused effort
    PURE_FUN_RECOVERY = "PURE_FUN_RECOVERY"    # guilt-free rest / leisure

class GoalStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    RETIRED = "RETIRED"

class EventType(str, Enum):
    CONFIRMATION = "CONFIRMATION"        # water / food / stretch / posture / walk taps
    MODE_TRANSITION = "MODE_TRANSITION"  # enter a UserMode
    QUIET_MOMENT = "QUIET_MOMENT"
    MEDIA_CAPTURED = "MEDIA_CAPTURED"    # lifecycle record; bytes live in media_assets

class ConfirmationKind(str, Enum):
    WATER = "WATER"
    FOOD_CLEAN = "FOOD_CLEAN"
    STRETCH = "STRETCH"
    POSTURE_RESET = "POSTURE_RESET"
    WALK = "WALK"

class MediaKind(str, Enum):
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"    # ambient capsule, 5-10 s
    VOICE = "VOICE"    # voice scrap / 2 AM spark

class TranscriptState(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    MANUAL_TEXT = "MANUAL_TEXT"    # user-supplied fallback text
    FAILED = "FAILED"

class RecapPeriod(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"  # contract only; generation is post-V1
    YEARLY = "YEARLY"    # contract only; generation is post-V1

class GenerationStatus(str, Enum):
    PENDING = "PENDING"
    GENERATED = "GENERATED"          # Gemini output passed validation
    FALLBACK = "FALLBACK"            # deterministic fallback used
    FAILED = "FAILED"                # observable failure; never silent
```

## 2. Typed Models (Pydantic)

These models are the locked V1 shapes. They may not be renamed or reshaped without an approved scope change recorded in `status.md`.

```python
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class ErrorResponse(BaseModel):
    code: str                 # e.g. "GOAL_CAP_REACHED", "MEDIA_LIMIT_EXCEEDED"
    message: str              # human-readable, non-shaming
    details: dict = Field(default_factory=dict)

class EventIn(BaseModel):
    type: EventType
    kind: Optional[ConfirmationKind] = None   # required iff type == CONFIRMATION
    mode: Optional[UserMode] = None           # required iff type == MODE_TRANSITION
    occurred_at: Optional[datetime] = None    # server time is authority if absent
    idempotency_key: str                      # client-generated; dedupes double taps

class GoalItem(BaseModel):
    id: UUID
    title: str
    status: GoalStatus
    created_at: datetime
    resolved_at: Optional[datetime] = None
    age_days: int            # computed at read time from user timezone; never stored

class MediaAssetMeta(BaseModel):
    id: UUID
    kind: MediaKind
    captured_at: datetime
    mime_type: str
    byte_length: int
    duration_sec: Optional[float] = None     # AUDIO/VOICE only
    transcript_state: TranscriptState
    transcript_text: Optional[str] = None
    # storage_key is NEVER returned to the client

class ModeInterval(BaseModel):
    mode: UserMode
    started_at: datetime
    ended_at: Optional[datetime] = None       # None = current mode
    duration_min: Optional[int] = None        # deterministic; never from the LLM

class DailyContext(BaseModel):
    """Deterministic aggregator output — the ONLY structured input to Gemini."""
    user_id: UUID
    local_date: date
    timezone: str                            # IANA name, e.g. "Asia/Kolkata"
    confirmations: dict                      # ConfirmationKind -> count / bool
    quiet_moments: int
    mode_intervals: List[ModeInterval]
    ideas: List[dict]                        # voice scraps w/ transcript_text, captured_at
    media_asset_ids: List[UUID]              # references only, no bytes/paths
    goals: List[GoalItem]                    # active goals with age_days
    evidence_event_ids: List[UUID]           # every claim must trace here

class Recap(BaseModel):
    id: UUID
    user_id: UUID
    period_type: RecapPeriod
    period_start: date
    period_end: date
    narrative: str
    insights: List[dict]                     # each insight cites evidence_event_ids
    highlight_media_ids: List[UUID]
    directive_for_next_cycle: Optional[str] = None
    source_recap_ids: List[UUID]             # WEEKLY consumes DAILY recap ids
    status: GenerationStatus
    created_at: datetime

class MorningDirective(BaseModel):
    id: UUID
    user_id: UUID
    for_date: date
    content: str                             # small, concrete, non-coercive
    source_recap_id: Optional[UUID] = None
    status: GenerationStatus
    shown_at: Optional[datetime] = None      # display dedupe; no duplicate generation
```

## 3. API Surface (V1)

| Method | Path | Purpose | Notes |
|---|---|---|---|
| `POST` | `/events` | ingest `EventIn` | idempotent on `idempotency_key` |
| `GET` / `POST` | `/mode` | current mode / transition | backend validates ordering + derives durations |
| `GET` / `POST` | `/goals` | list (with `age_days`) / add | add fails `409 GOAL_CAP_REACHED` at 3 ACTIVE |
| `POST` | `/goals/{id}/complete` · `/goals/{id}/retire` | resolve, freeing a slot | |
| `POST` | `/media` | multipart upload → `MediaAssetMeta` | server-generated storage key; size/duration/MIME limits |
| `GET` / `DELETE` | `/media/{id}` | stream bytes / delete | owner + auth required; no paths exposed |
| `GET` | `/timeline?from=&to=` | events + media refs for private feed | |
| `GET` | `/recaps?period=DAILY&date=` | fetch recap | WEEKLY supported; MONTHLY/YEARLY return empty post-V1 |
| `GET` | `/directive/today` | today's `MorningDirective` | generates idempotently on first open |
| `POST` | `/internal/run/{daily\|weekly}` | authenticated job trigger | local MVP; no public exposure |
| `GET` | `/health` | liveness | unauthenticated, no data |

## 4. Cross-Cutting Rules (Locked HWGA01)

- **Auth:** single-user bearer token (`Authorization: Bearer <token>`) on every route except `GET /health`. Token is provisioned by a backend bootstrap CLI into the database (hashed at rest), not an env var; rotate by re-running the CLI and re-entering the token on the phone. Threat assumption: private single-user app; ngrok ingress is treated as hostile, so auth is mandatory with the tunnel active.
- **Time:** all persisted timestamps UTC; all period windows computed in `users.timezone` (IANA; default `Asia/Kolkata`, editable). Events arriving after a period closed are backfilled via `occurred_at` into the period they belong to; an already-generated recap for that period is marked stale and regenerated once on next fetch under the same idempotency key. Mode durations are derived from transitions by deterministic code only.
- **Idempotency:** `EventIn.idempotency_key` is unique per user; recap/directive generation is unique on `(user_id, period_type, period_start)` / `(user_id, for_date)`. Retries and duplicate taps never create duplicates.
- **Rule of 3 enforcement:** serialized transaction — the service takes a per-user lock (`SELECT ... FOR UPDATE` on the user row), counts `ACTIVE` goals, and rejects the insert with `409 GOAL_CAP_REACHED` if the count is 3. Not client-side.
- **Media limits (V1):** IMAGE ≤ 10 MB, MIME `image/jpeg|image/png|image/webp`; AUDIO and VOICE ≤ 60 s and ≤ 15 MB, MIME `audio/mp4 (m4a)|audio/aac|audio/mpeg|audio/wav`. Ambient capsules are prompted at 5–10 s in UX but the server cap is 60 s. Retention: user deletes manually; no auto-expiry in V1. Violations return `413 MEDIA_LIMIT_EXCEEDED` / `422 UNSUPPORTED_MEDIA_TYPE`. Client never sees `storage_key` or filesystem paths; media served only via authenticated `/media/{id}`.
- **Errors:** every error response uses `ErrorResponse`; auth failures `401`, ownership violations `403`/`404` (no existence leaks), validation `422`, goal cap `409`, upload limits `413`. Known codes: `GOAL_CAP_REACHED`, `MEDIA_LIMIT_EXCEEDED`, `UNSUPPORTED_MEDIA_TYPE`, `INVALID_MODE_TRANSITION`, `UNAUTHORIZED`, `NOT_FOUND`, `VALIDATION_ERROR`, `GENERATION_FAILED`.
- **Missing data:** missing = unknown, not negative. `DailyContext` omits unlogged kinds; the narrative must never assert something did not happen.
- **Generation retry/fallback:** Gemini calls are timeout-bounded with at most 2 retries; on exhaustion a deterministic fallback receipt is persisted with `status=FALLBACK`. `FAILED` is only for observable persistence errors — never silent.
- **Gemini boundary:** Gemini receives `DailyContext` (or stored recap objects for weekly) only — no raw media, no event history dumps, no database access. **Single approved exception:** VOICE audio bytes may be sent to the Gemini API solely for speech-to-text; only the transcript enters `DailyContext`. No IMAGE or AUDIO bytes are ever sent.

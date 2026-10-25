# HWGA V2 Contracts — Additions Only

- **Document ID:** CONTRACTS-HWGA-V2
- **Status:** **DRAFT** — locked at V2A with user approval
- **Authority:** V1 [`contracts.md`](../contracts.md) remains the single source for all V1 enums/models/API. This file may ADD surface only; it may not rename, reshape, or relax V1 items.

## 1. New Typed Models (proposed)

```python
class WidgetState(BaseModel):
    """One lightweight read model for both home-screen widgets. Everything
    on it is already computable from V1 contracts — this is a convenience
    aggregate, not a new truth."""
    generated_at: datetime                              # server UTC; widget shows freshness
    mode: Optional[ModeInterval]                        # current open interval or None (V1 model)
    today_confirmations: dict[ConfirmationKind, int]    # V1 enum keys; logged kinds only (missing = unknown)
    quiet_moments_today: int
    goals_active: int
    oldest_goal_age_days: Optional[int]                 # reuses V1 age_days computation verbatim; never widget-computed
    directive_line: Optional[str]                       # ≤120 chars, server-truncated, single line, no newlines;
                                                        # may be FALLBACK-derived
    directive_status: Optional[GenerationStatus]
    receipt_status: Optional[GenerationStatus]          # today's daily recap, if any
    receipt_stale: bool                                 # V1 staleness rule for recaps (contracts.md), unmodified
```

```python
class PipelineKind(str, Enum):
    RECEIPT = "RECEIPT"
    DIRECTIVE = "DIRECTIVE"
    WEEKLY = "WEEKLY"

class PipelineStatusItem(BaseModel):
    """One row of the in-app pipeline surface."""
    kind: PipelineKind
    period_label: str            # display-only, server-formatted — exactly:
                                 #   RECEIPT/DIRECTIVE -> "Today" or "YYYY-MM-DD"
                                 #   WEEKLY -> "Week YYYY-MM-DD – YYYY-MM-DD"
    status: GenerationStatus     # GENERATED | FALLBACK | FAILED | PENDING (missing row)
    stale: bool
    created_at: Optional[datetime]
    source_recap_ids: List[UUID] # weekly only; empty otherwise
```

## 2. New API Surface (proposed)

| Method | Path | Purpose | Notes |
|---|---|---|---|
| `GET` | `/widget/state` | single authenticated aggregate for widgets | ~1 KB; no media refs, no narrative; all values server-computed |
| `GET` | `/pipeline/status` | in-app pipeline surface rows | today's receipt, today's directive, current week roll-up |

`GET /widget/state` 200 response is exactly the `WidgetState` JSON — normative example:

```json
{
  "generated_at": "2026-10-25T18:30:00Z",
  "mode": null,
  "today_confirmations": {"WATER": 3, "STRETCH": 1},
  "quiet_moments_today": 0,
  "goals_active": 2,
  "oldest_goal_age_days": 4,
  "directive_line": "Protect the morning: one clean meal before noon.",
  "directive_status": "GENERATED",
  "receipt_status": "PENDING",
  "receipt_stale": false
}
```

Nullability: every field except `generated_at`, `today_confirmations`, `quiet_moments_today`, `goals_active`, and `receipt_stale` may be `null`. Clients/widgets must ignore unknown fields (forward-compatible additions only).

On-demand generation uses `POST /internal/run/{daily|weekly}` — a V1-internal route now triggered from user UI. V2A must decide and record: (a) whether it stays under `/internal/` or is re-exposed under a user-facing path in the V2 contract, and (b) its regenerate semantics and cooldown/rate-limit (tap-spam costs real LLM calls). No implementation may choose silently.

Everything else the widgets need already exists: `POST /events` (idempotent `idempotency_key`), `GET`/`POST /mode`, `GET /timeline`, `GET /recaps`, `GET /directive/today`.

## 3. Deep-Link Contract (proposed)

App-internal route names the widgets may open — implemented as Android `PendingIntent` deep-links; each resolves even when the app process is cold:

| Target | Deep-link | Lands on |
|---|---|---|
| Receipt | `hwga://receipt/today` | ReceiptScreen for today |
| Directive | `hwga://directive` | HomeScreen directive card |
| Timeline | `hwga://today` | Today screen |
| Goals | `hwga://goals` | Goals screen |
| Auth | `hwga://auth` | Token screen (widget auth-required state) |

Rules: the auth check runs before route resolution on every deep-link — a cold start with a missing/expired token always lands on the Token screen regardless of target. Unknown or malformed `hwga://` URIs fall back to HomeScreen (never crash, never no-op silently in logs-only fashion — show the default screen).

## 4. V2 Error Codes (proposed)

Reuses V1 `ErrorResponse`. No new codes expected; candidates if needed during V2A: `WIDGET_STALE_STATE` (never currently needed — staleness is data, not an error).

## 5. Carried Rules

- Auth: unchanged — bearer on every route including `/widget/state` and `/pipeline/status`.
- Idempotency: unchanged — widget taps must send a fresh UUID `idempotency_key` per user tap; replays return the stored event, never a duplicate.
- Missing data: unchanged — `today_confirmations` omits unlogged kinds; `receipt_status` of a missing recap is represented as `PENDING` + `receipt_stale=false`, not an error.
- Media: unchanged — nothing media-related appears in any widget payload.

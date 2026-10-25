# HWGA V2 Contracts — Additions Only

- **Document ID:** CONTRACTS-HWGA-V2
- **Status:** **LOCKED** — V2A, 2026-10-25, user approved (decisions V2-D02…V2-D06 in `status_v2.md`)
- **Authority:** V1 [`contracts.md`](../contracts.md) remains the single source for all V1 enums/models/API. This file may ADD surface only; it may not rename, reshape, or relax V1 items.

## 1. New Typed Models (locked)

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

## 2. New API Surface (locked)

| Method | Path | Purpose | Notes |
|---|---|---|---|
| `GET` | `/widget/state` | single authenticated aggregate for widgets | ~1 KB; no media refs, no narrative; all values server-computed |
| `GET` | `/pipeline/status` | in-app pipeline surface rows | today's receipt, today's directive, current week roll-up |
| `POST` | `/generate/{kind}` | user-facing on-demand generation, `kind` ∈ `receipt \| directive \| weekly` | V2-D06: new route; `POST /internal/run/{daily\|weekly}` stays internal-only |

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

`POST /generate/{kind}` (V2-D06, locked):

- **Semantics:** regenerates the artifact for the **current period** unconditionally, using data accumulated so far ("data so far" semantics — the trigger time does not need to be the period boundary). A regenerated artifact replaces the stored one for the same `(user_id, period_type, period_start)` key and clears its stale flag. `receipt`/`weekly` return `Recap`; `directive` returns `MorningDirective` (V1 models, unmodified).
- **Cooldown:** max one manual trigger per `kind` per user per 60 s; excess calls return `429` with `ErrorResponse` code `GENERATION_COOLDOWN` (new V2 code, §4).
- The V1-internal `POST /internal/run/{daily|weekly}` route is unchanged and stays internal; the app UI must call `/generate/...` only.

Everything else the widgets need already exists: `POST /events` (idempotent `idempotency_key`), `GET`/`POST /mode`, `GET /timeline`, `GET /recaps`, `GET /directive/today`.

## 3. Deep-Link Contract (locked)

App-internal route names the widgets may open — implemented as Android `PendingIntent` deep-links; each resolves even when the app process is cold:

| Target | Deep-link | Lands on |
|---|---|---|
| Receipt | `hwga://receipt/today` | ReceiptScreen for today |
| Directive | `hwga://directive` | HomeScreen directive card |
| Timeline | `hwga://today` | Today screen |
| Goals | `hwga://goals` | Goals screen |
| Auth | `hwga://auth` | Token screen (widget auth-required state) |

Rules: the auth check runs before route resolution on every deep-link — a cold start with a missing/expired token always lands on the Token screen regardless of target. Unknown or malformed `hwga://` URIs fall back to HomeScreen (never crash, never no-op silently in logs-only fashion — show the default screen).

## 4. V2 Error Codes (locked)

Reuses V1 `ErrorResponse`. One new code added at V2A lock:

| Code | HTTP | Meaning |
|---|---|---|
| `GENERATION_COOLDOWN` | 429 | `POST /generate/{kind}` triggered again within 60 s for the same kind |

`WIDGET_STALE_STATE` was considered and rejected — staleness is data, not an error.

## 5. Carried Rules

- Auth: unchanged — bearer on every route including `/widget/state` and `/pipeline/status`.
- Idempotency: unchanged — widget taps must send a fresh UUID `idempotency_key` per user tap; replays return the stored event, never a duplicate.
- Missing data: unchanged — `today_confirmations` omits unlogged kinds; `receipt_status` of a missing recap is represented as `PENDING` + `receipt_stale=false`, not an error.
- Media: unchanged — nothing media-related appears in any widget payload.

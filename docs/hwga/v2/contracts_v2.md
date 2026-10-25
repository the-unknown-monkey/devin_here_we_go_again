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
    generated_at: datetime                    # server UTC; widget shows freshness
    mode: Optional[ModeInterval]              # current open interval or None
    today_confirmations: dict                 # ConfirmationKind -> count (logged kinds only; missing = unknown)
    quiet_moments_today: int
    goals_active: int
    oldest_goal_age_days: Optional[int]       # from server-computed age_days; never widget-computed
    directive_line: Optional[str]             # single short line; may be FALLBACK-derived
    directive_status: Optional[GenerationStatus]
    receipt_status: Optional[GenerationStatus]  # today's daily recap, if any
    receipt_stale: bool
```

```python
class PipelineStatusItem(BaseModel):
    """One row of the in-app pipeline surface."""
    kind: str                    # "RECEIPT" | "DIRECTIVE" | "WEEKLY"
    period_label: str            # e.g. "Today", "2026-10-25", "Week 10-19 – 10-25"
    status: GenerationStatus     # GENERATED | FALLBACK | FAILED | PENDING(missing)
    stale: bool
    created_at: Optional[datetime]
    source_recap_ids: List[UUID] # weekly only; empty otherwise
```

## 2. New API Surface (proposed)

| Method | Path | Purpose | Notes |
|---|---|---|---|
| `GET` | `/widget/state` | single authenticated aggregate for widgets | ~1 KB; no media refs, no narrative; all values server-computed |
| `GET` | `/pipeline/status` | in-app pipeline surface rows | today's receipt, today's directive, current week roll-up |

Everything else the widgets need already exists: `POST /events` (idempotent `idempotency_key`), `GET`/`POST /mode`, `GET /timeline`, `GET /recaps`, `GET /directive/today`, `POST /internal/run/{daily|weekly}`.

## 3. Deep-Link Contract (proposed)

App-internal route names the widgets may open — implemented as Android `PendingIntent` deep-links; each resolves even when the app process is cold:

| Target | Deep-link | Lands on |
|---|---|---|
| Receipt | `hwga://receipt/today` | ReceiptScreen for today |
| Directive | `hwga://directive` | HomeScreen directive card |
| Timeline | `hwga://today` | Today screen |
| Goals | `hwga://goals` | Goals screen |
| Auth | `hwga://auth` | Token screen (widget auth-required state) |

## 4. V2 Error Codes (proposed)

Reuses V1 `ErrorResponse`. No new codes expected; candidates if needed during V2A: `WIDGET_STALE_STATE` (never currently needed — staleness is data, not an error).

## 5. Carried Rules

- Auth: unchanged — bearer on every route including `/widget/state` and `/pipeline/status`.
- Idempotency: unchanged — widget taps must send a fresh UUID `idempotency_key` per user tap; replays return the stored event, never a duplicate.
- Missing data: unchanged — `today_confirmations` omits unlogged kinds; `receipt_status` of a missing recap is represented as `PENDING` + `receipt_stale=false`, not an error.
- Media: unchanged — nothing media-related appears in any widget payload.

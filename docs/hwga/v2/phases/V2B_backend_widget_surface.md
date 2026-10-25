# Phase V2B: Backend Widget Surface

- **Phase ID:** V2B | **Branch:** `main` | **Status:** Planned
- **Dependency:** V2A locked contracts
- **Scope:** backend only — `GET /widget/state` (+ models). No Android/Flutter work.

## 1. Goal

Ship the single lightweight aggregate both widgets consume, built entirely from existing repositories and services. ~1 KB, server-computed only, bearer-gated, no media/narrative.

## 2. Deliverables (per implementation_v2.md §2)

- `app/schemas/contracts.py` — add `WidgetState` + `PipelineStatusItem` (V2 contract shapes; PipelineStatusItem may be added here or in V2E per contract lock)
- `app/services/widget_state.py` — builds `WidgetState` from `ModeRepository`, `EventRepository`, `GoalRepository`, `RecapRepository`, `Directive` service; user-local day window per D20
- `app/api/routers/widget.py` — `GET /widget/state`, `require_auth`, wires into `app/main.py`
- `backend/tests/test_widget_state.py`

## 3. Rules

- All values server-side: `mode` open interval w/ derived `duration_min`; `today_confirmations` counts for **logged kinds only** (missing = unknown); `quiet_moments_today`; `goals_active` + `oldest_goal_age_days` (reuse `age_days` logic — never recompute differently); `directive_line` + `directive_status` (stored row only — **do not trigger generation** from this endpoint); `receipt_status` + `receipt_stale` (stored row only; missing → `PENDING`).
- No reads that cause writes: `/widget/state` must be side-effect-free (no recap/directive generation).
- Errors → V1 `ErrorResponse`; unauthenticated → 401.
- `generated_at` = server UTC now.

## 4. Verification

```powershell
cd backend && docker compose up -d db-test && uv run pytest tests -q -ra
# plus live curl against dev stack: 401 without token; 200 shape match with token
```

Record exact output. Widget surface contract-checks: response keys match `contracts_v2.md` §1 exactly.

## 5. Exit Criteria

- Suite green including new tests; live curl evidence recorded
- Two-Step Commit Protocol → push

## 6. Copy-Paste Prompt

```text
Please execute Phase V2B: Backend Widget Surface on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short

Read docs/hwga/v2/ contracts_v2.md (LOCKED), implementation_v2.md, status_v2.md, and V1 contracts.md + trd.md. Inspect the real backend: app/api/routers/, app/services/, app/db/repositories/, app/schemas/contracts.py — reuse existing repository/service methods; never recompute age_days or durations differently. If any doc contradicts live code or installed dependency APIs, stop, record the discrepancy in status_v2.md, and ask before proceeding.

Implement GET /widget/state exactly per the locked contract: bearer-gated, side-effect-free (never triggers generation), logged-kinds-only confirmations, stored-row statuses, V1 ErrorResponse. Add WidgetState to app/schemas/contracts.py, app/services/widget_state.py, app/api/routers/widget.py wired in app/main.py, and backend/tests/test_widget_state.py.

Run `docker compose up -d db-test`, `uv run pytest tests -q -ra`, and a live curl check (401 unauth / 200 with token). Record real output in status_v2.md and apply the Two-Step Commit Protocol. Stop at the phase boundary.
```

# Phase V2E: Pipeline Surface & On-Demand Generation

- **Phase ID:** V2E | **Branch:** `main` | **Status:** Planned
- **Dependency:** V2B (`PipelineStatusItem` contract)
- **Scope:** in-app pipeline visibility + user-facing generation triggers. Backend + Flutter.

## 1. Goal

Give the user (a) a screen listing what the pipeline produced and its status, and (b) explicit "generate now" actions that produce a receipt/directive/weekly from data accumulated so far — reusing V1's lazy generation, never a parallel pipeline.

## 2. Deliverables

- `app/services/pipeline_status.py` — builds `PipelineStatusItem`s for today's receipt, today's directive, current week (status/stale/created_at/source_recap_ids; missing → `PENDING`)
- `app/api/routers/pipeline.py` — `GET /pipeline/status`, bearer-gated, side-effect-free; wired in `app/main.py`
- `lib/features/pipeline/pipeline_screen.dart` — rows per item with status badge (GENERATED/FALLBACK/FAILED/PENDING), stale marker, timestamps, tap-through to the artifact screen
- On-demand actions: "Generate receipt now" / "Refresh directive" / "Build weekly" — calling the existing surfaces (`GET /recaps` lazy-generates; `POST /internal/run/{daily|weekly}` force-runs). UI states: generating → done/failed; copy makes clear it's "from data so far"
- `lib/core/api/api_client.dart` gains `getPipelineStatus` + internal-run methods; models per contract

## 3. Rules (hard)

- On-demand must not weaken idempotency or stale rules: same `(user, period_type, period_start)` still dedupes; a regenerate only happens through the contract's stale path or an explicit `internal/run` — follow the recorded decision (V2-D06) on whether `internal/run` force-regenerates (mark stale then generate), its exposure path, and its cooldown/rate-limit; if V2-D06 is unresolved, decide + record it before implementing triggers.
- Directive same-day uniqueness stands (contract); "refresh directive" either shows the stored one or follows the recorded decision — never a silent second directive.
- Status badges must be honest: FALLBACK is not dressed as GENERATED; FAILED shows a retry affordance.
- No pipeline internals leak: row shows status/stale/timestamps/evidence ids only — no prompts, no raw context.

## 4. Verification

- Backend: new `test_pipeline_status.py` (missing→PENDING, GENERATED/FALLBACK rows, stale flags, weekly source ids); full suite green
- Flutter: widget tests for all status states + on-demand flows; `dart format`/`analyze`/`test` green
- Live dev-stack check: `GET /pipeline/status` 401/200; generate-now produces a real row observable on the endpoint

## 5. Exit Criteria

- Gates green + live evidence in `status_v2.md`; decision on `internal/run` semantics recorded
- Two-Step Commit Protocol → push

## 6. Copy-Paste Prompt

```text
Please execute Phase V2E: Pipeline Surface & On-Demand Generation on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short

Read docs/hwga/v2/ contracts_v2.md, implementation_v2.md, status_v2.md, V1 contracts.md §3-4, and inspect the real code: app/services/{recaps,directives}.py, app/api/routers/{recaps,directive}.py, lib/features/recaps/, lib/core/api/. If any doc contradicts live code or installed dependency APIs, stop, record the discrepancy in status_v2.md, and ask before proceeding.

Deliverable: GET /pipeline/status (side-effect-free PipelineStatusItem rows: today's receipt, today's directive, current week), a Flutter pipeline screen with honest GENERATED/FALLBACK/FAILED/PENDING badges + stale markers + tap-through, and user-facing generate-now actions reusing lazy GET /recaps and POST /internal/run/{daily|weekly} — never a parallel pipeline. Record and document the chosen internal/run regenerate semantics; directive same-day uniqueness per contract.

Verify: new backend tests + full suite, Flutter widget tests/format/analyze, live curl 401/200 + a real generate-now cycle. Evidence in status_v2.md, Two-Step Commit, push. Stop at the phase boundary.
```

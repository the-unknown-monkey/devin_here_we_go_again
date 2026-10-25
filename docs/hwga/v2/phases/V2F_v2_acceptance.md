# Phase V2F: V2 Regression & Nothing Phone 2a Widget Acceptance

- **Phase ID:** V2F | **Branch:** `main` | **Status:** Planned
- **Dependency:** V2A–V2E complete
- **Scope:** comprehensive V2 regression + physical widget acceptance + runbook update. No new features.

## 1. Acceptance Matrix

1. Full backend suite on disposable Postgres (`uv run pytest tests -q -ra`).
2. Flutter `dart format --set-exit-if-changed lib test` / `flutter analyze` / `flutter test` / `flutter build apk --debug`.
3. Widget security: no token readable in widget logs/prefs dumps; `GET /widget/state` 401 unauth via ngrok; widget degrades to auth-required after token rotation.
4. Widget journeys on A142 (manual, user-confirmed): add both widgets → tap each chip → events land in `/timeline` → force-close app → taps still work → airplane-mode failure honesty → mode flip lands in `/mode` → hook-line deep-links cold-start to correct screens → counts refresh per V2A cadence.
5. Privacy check: widget surfaces show counts/chips/one line only — screenshot review for leaks.
6. Pipeline surface: statuses match DB truth; on-demand generation produces a real artifact end-to-end.
7. ngrok re-verified: only 8000 exposed, auth intact, Postgres unreachable.

## 2. Runbook Update

Update `docs/hwga/runbook.md` (V1 file) only after checks pass and user confirms: add widget add/remove lifecycle, refresh cadence notes, token-rotation effect on widgets, troubleshooting rows observed during V2.

## 3. Exit Criteria

- Matrix pass or fixed+rerun; user explicitly confirms widget acceptance on A142
- `status_v2.md` records real evidence + V2 acceptance decision
- Two-Step Commit Protocol → push; handoff summary

## 4. Copy-Paste Prompt

```text
Please execute Phase V2F: V2 Regression & Nothing Phone 2a Widget Acceptance on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short
  %LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe devices

Read all docs/hwga/v2/ docs including every status_v2.md evidence entry, V1 status.md §5, and this phase file. Treat any check without recorded evidence as unverified.

Run the repository's real commands (backend pytest on disposable DB; flutter format/analyze/test/build). Coordinate every manual widget step on my Nothing Phone 2a — I execute and report; never claim acceptance without my confirmation. Verify widget security (401 unauth, no token leaks), privacy surface (counts/chips/one line only), offline honesty, idempotent taps, cold-start deep-links, and token-rotation degradation. Update runbook.md only with verified commands after I confirm.

Finish with the Two-Step Commit Protocol (implementation commit → hash → status_v2.md docs commit with the V2 acceptance decision → git push origin main). Report both hashes, remaining limitations, and the V2 decision.
```

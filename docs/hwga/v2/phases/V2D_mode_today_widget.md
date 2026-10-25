# Phase V2D: Mode + Today Hook Widget

- **Phase ID:** V2D | **Branch:** `main` | **Status:** Planned
- **Dependency:** V2C (widget plumbing proven)
- **Scope:** Android widget #2 + deep-links into the app.

## 1. Goal

A widget showing the current mode (flip between LOCKED_IN / PURE_FUN_RECOVERY via `POST /mode`) plus one rotating hook line chosen server-side-priority: directive clause → "receipt ready" (receipt_status/stale) → oldest goal age. Tapping the line deep-links to the matching screen.

## 2. Deliverables

- `kotlin/.../widget/ModeTodayWidgetProvider.kt` + `res/layout/widget_mode_today.xml` + `res/xml/mode_today_widget_info.xml` + manifest receiver
- Deep-link plumbing: `MainActivity.kt` handles widget `PendingIntent` URIs (`hwga://receipt/today`, `hwga://directive`, `hwga://goals`, `hwga://auth`, `hwga://today`); Dart-side route resolution incl. cold-start
- Widget hook line = `directive_line`/`receipt_status`/`oldest_goal_age_days` from `/widget/state` — display priority per contract; tap area deep-links; refresh follows the V2A cadence
- Mode flip uses the same honest pending/failure pattern as V2C

## 3. Rules (hard)

- Hook line length-capped (fit one line, ellipsize); never renders narrative/insights/media — widget stays counts+chips+one line per privacy invariant.
- Non-shaming copy only (reuse app language: "Rest & fun", goal age as neutral fact).
- Deep-link targets resolve cold: app closed → intent → correct screen after auth check; missing token → token screen.
- Mode flip never invents a transition: same-mode taps are disabled/no-op; failures revert the pill.

## 4. Verification

- Same static gates as V2C plus device proof on A142: add widget → flip mode → `GET /mode` reflects it → timeline shows MODE_TRANSITION; tap hook line cold-start → correct screen; missing-token path → auth screen.

## 5. Exit Criteria

- Green gates + device evidence in `status_v2.md`. Device proof requires the user executing steps on the A142 and reporting — emulator results and agent self-certification do not count.
- Two-Step Commit Protocol → push

## 6. Copy-Paste Prompt

```text
Please execute Phase V2D: Mode + Today Hook Widget on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short
  %LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe devices

Read docs/hwga/v2/ docs + status_v2.md (V2A decisions, V2C evidence) and inspect the real widget plumbing added in V2C plus lib/app/app.dart routing and features/recaps/. Verify any APIs against installed versions. If any doc contradicts live code or installed dependency APIs, stop, record the discrepancy in status_v2.md, and ask before proceeding.

Deliverable: second home-screen widget — current mode pill with honest flip (POST /mode), one hook line sourced from /widget/state fields in contract priority order (directive clause, receipt-ready, oldest goal age), deep-links (hwga:// URIs) resolving cold-start into ReceiptScreen/HomeScreen/GoalsScreen/TokenScreen. One line max, ellipsized; counts+chips+one-line only — no narrative/insights/media on the home surface.

Verify gates (format/analyze/test/pytest) then device proof: mode flip lands in /mode + timeline MODE_TRANSITION; cold-start deep-links reach the right screens; no-token → auth screen. Record evidence, Two-Step Commit, push. Stop at the phase boundary.
```

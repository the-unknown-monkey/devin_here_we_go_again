# Phase V2C: Quick-Taps Widget

- **Phase ID:** V2C | **Branch:** `main` | **Status:** Planned
- **Dependency:** V2B (`GET /widget/state` live)
- **Scope:** Android widget #1 — one-tap baseline logging without opening the app.

## 1. Goal

A resizable home-screen widget with chips for WATER, FOOD_CLEAN, STRETCH, POSTURE_RESET, WALK, QUIET_MOMENT. Each tap fires `POST /events` with a fresh UUID `idempotency_key`, shows a per-chip confirm state, and displays today's counts from `/widget/state`.

## 2. Deliverables

- `kotlin/ai/hwga/hwga/widget/QuickTapsWidgetProvider.kt` — `AppWidgetProvider` + broadcast receiver for tap actions (or the V2A-chosen `home_widget` interactivity)
- `kotlin/.../widget/WidgetApi.kt` — native `POST /events` + `GET /widget/state` with bearer from the V2A token path; never logs the token
- `kotlin/.../widget/WidgetStore.kt` — token read + last `WidgetState` cache
- `res/layout/widget_quick_taps.xml`, `res/xml/quick_taps_widget_info.xml`, manifest `<receiver>` + `<meta-data>`
- `lib/core/widget_bridge.dart` — pushes base URL/token/state to native + refreshes widget on app events (per V2A bridge decision)
- Failure states rendered on the widget: offline/failed-tap (honest, with retry affordance), no-token (deep-link to `hwga://auth`)

## 3. Rules (hard)

- Fresh `idempotency_key` UUID **per user tap** — double-taps rely on server idempotency anyway; keys are not reused.
- Optimistic chip feedback allowed only as a transient "sending" state — a failed call must visibly undo it. No fake logs.
- RemoteViews constraints: no custom fonts/animations; chips must meet touch-target minimums; respect dark/light theme.
- No new manifest permissions. Widget must not start foreground services or schedule workers.
- Cold-install path honored (V2A decision): widget works (or degrades honestly) even if the Flutter app was never opened.

## 4. Verification

- `cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test` green (bridge logic unit-tested platform-free)
- `cd backend && uv run pytest tests -q -ra` green (unchanged, regression)
- Device proof on A142: add widget → tap Water → `GET /timeline` shows the CONFIRMATION; tap while offline → honest failure; repeat tap after reconnect → single event (idempotency), verify count in `/widget/state`.

## 5. Exit Criteria

- All checks pass; device tap → DB event proven with real output in `status_v2.md`
- Two-Step Commit Protocol → push

## 6. Copy-Paste Prompt

```text
Please execute Phase V2C: Quick-Taps Widget on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short
  %LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe devices

Read docs/hwga/v2/ (esp. locked contracts_v2.md, implementation_v2.md, status_v2.md V2A decisions) and inspect the real code first: flutter/android/app/src/main/ (manifest, MainActivity), lib/core/{api,config}/, backend widget/state endpoint. Use only the bridge/token path decided in V2A; verify any package APIs against the resolved version — never assume names.

Deliverable: home-screen quick-taps widget (WATER/FOOD_CLEAN/STRETCH/POSTURE_RESET/WALK/QUIET_MOMENT) that POSTs /events with a fresh UUID idempotency_key per tap, shows sending/confirm/failure honestly, renders today counts from /widget/state, handles no-token and cold-install per V2A decisions. RemoteViews-safe UI, no new permissions, no background services.

Verify: dart format/analyze/test, backend pytest, then real device proof — tap produces a /timeline event, offline fails honestly, reconnect produces exactly one event. Record evidence in status_v2.md, Two-Step Commit Protocol, push. Stop at the phase boundary.
```

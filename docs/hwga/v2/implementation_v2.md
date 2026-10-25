# HWGA V2 Implementation Map

- **Document ID:** IMPL-HWGA-V2
- **Status:** Draft — file paths below are written **against the real V1 tree** (verified 2026-10-25); "exists" entries were read, "new" entries are planned.

## 1. Real V1 Anchors (verified this session)

| Area | Verified fact |
|---|---|
| Flutter entry | `lib/main.dart` → `runApp(const HwgaApp())`; `lib/app/app.dart` |
| API client | `lib/core/api/api_client.dart` — typed, bearer via `tokenProvider`, 10 s timeout, single retry on network errors for idempotent GETs only |
| Token | `lib/core/api/token_store.dart` — `flutter_secure_storage` key `hwga_auth_token`; `MemoryTokenStore` for tests |
| Config | `lib/core/config/app_config.dart` — `HWGA_API_BASE_URL` / `HWGA_DEV_TOKEN` dart-defines only; default `http://127.0.0.1:8000` |
| Features | `baselines/`, `modes/`, `goals/`, `timeline/`, `vault/`, `recaps/` (receipt, directive card, chronology), `auth/`, `connection/`, `home/` |
| Android | `android/app/src/main/AndroidManifest.xml` — INTERNET+CAMERA+RECORD_AUDIO, `usesCleartextTraffic="true"`, **no receivers**; `MainActivity.kt` = plain `FlutterActivity` |
| Backend | FastAPI app factory `app/main.py`; routers: health, me, events(+timeline), mode, goals, media, recaps(+`/internal/run/{job}`), directive; `require_auth` in `app/core/security.py`; SQLAlchemy+Alembic head `5e1d2551dffb` |
| Agent stack | `app/agents/` — gemini provider (`GEMINI_MODEL`, ≤2 retries), fact_guard, chain_guard, three LangGraphs; daily/weekly/directive services |
| Deps | `pubspec.yaml`: http, flutter_secure_storage, image_picker, record, permission_handler ^12.0.3, audioplayers, http_parser, path_provider. **No widget package yet.** |

## 2. Planned V2 Layout

```text
flutter/android/app/src/main/
  kotlin/ai/hwga/hwga/
    MainActivity.kt                       # exists; gains widget deep-link dispatch (V2C/D)
    widget/
      QuickTapsWidgetProvider.kt          # new (V2C) — AppWidgetProvider + tap receiver
      ModeTodayWidgetProvider.kt          # new (V2D)
      WidgetApi.kt                        # new — native HTTP calls w/ bearer (or bridge delegate)
      WidgetStore.kt                      # new — token read + cached WidgetState
  res/
    layout/widget_quick_taps.xml          # new — RemoteViews layout
    layout/widget_mode_today.xml          # new
    xml/quick_taps_widget_info.xml        # new — appwidget-provider meta
    xml/mode_today_widget_info.xml        # new
flutter/lib/
  core/widget_bridge.dart                 # new — shares token/base URL + pushes state to native
  features/pipeline/pipeline_screen.dart  # new (V2E)
backend/app/
  api/routers/widget.py                   # new (V2B) — GET /widget/state
  api/routers/pipeline.py                 # new (V2E) — GET /pipeline/status
  services/widget_state.py                # new (V2B) — builds WidgetState from repos
  services/pipeline_status.py             # new (V2E)
backend/tests/
  test_widget_state.py, test_pipeline_status.py   # new
```

## 3. Open Technical Questions for V2A (must be answered with real probes, not assumptions)

1. **Bridge:** `home_widget` package vs fully native. Probe: can Kotlin read `hwga_auth_token` from the `flutter_secure_storage` shared-prefs file on the A142? (It uses EncryptedSharedPreferences on Android — natively readable, but verify.) If unreadable → token must be mirrored via a bridge at app runtime.
2. **Base URL on native side:** `HWGA_API_BASE_URL` is compile-time-only in Dart. Options: `MethodChannel` handoff, `BuildConfig` field, or `home_widget` data store. Decide + record.
3. **Interactive taps:** `home_widget` interactivity vs native `PendingIntent` broadcast → Kotlin-side POST. Android 15 supports interactive RemoteViews; verify minSdk (`flutter` default) and behavior on Nothing OS.
4. **Update cadence:** `updatePeriodMillis` floor is 30 min; whether tap-driven refresh + app-resume push suffices without a background worker.

## 4. Test Strategy

| Layer | Command | Target |
|---|---|---|
| Backend new routes | `cd backend && uv run pytest tests -q -ra` | disposable test DB (55533) |
| Flutter widget-side Dart | `cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test` | bridge/pipeline logic platform-free via injected fakes |
| Android widget | manual on A142 (V2F) | add-widget → tap → `/timeline` check → offline → token rotation |
| Native Kotlin unit tests | optional; prefer logic-thin widgets with logic in `services/` + Dart bridge where testable | — |

## 5. Phase ↔ File Matrix

| Phase | Primary files | Layer |
|---|---|---|
| V2A | `v2/contracts_v2.md` locked; `status_v2.md` decisions; bridge probe results | Docs + probes |
| V2B | `app/api/routers/widget.py`, `app/services/widget_state.py`, `schemas/contracts.py` (+V2 models), tests | Backend |
| V2C | `widget/QuickTapsWidgetProvider.kt`, layouts/xml, manifest receiver, `widget_bridge.dart` | Android+Flutter |
| V2D | `widget/ModeTodayWidgetProvider.kt`, deep-link dispatch in `MainActivity.kt`, app route handling | Android+Flutter |
| V2E | `app/api/routers/pipeline.py`, `services/pipeline_status.py`, `features/pipeline/` + on-demand triggers | Both |
| V2F | `runbook.md` update, `status_v2.md` evidence, V2 acceptance on A142 | Both |

# HWGA V2 Status Ledger

- **Project:** Here We Go Again (HWGA) — V2 (widgets + pipeline surface + on-demand)
- **Remote:** `https://github.com/the-unknown-monkey/devin_here_we_go_again.git`
- **Active Branch:** `main`
- **Baseline:** V1 ACCEPTED 2026-10-25 (HWGA08); V1 `status.md` holds decisions D01–D27 and all prior evidence
- **Ledger rule:** same as V1 — record evidence observed in this repository/machine only.

## 1. Decision Register

| ID | Decision question | Approved decision | Rationale |
|---|---|---|---|
| **V2-D01** | V2 scope? | D27 widgets (quick-taps + mode/today hook) + D26 (pipeline surface + on-demand generation) — all user-approved during HWGA08 | User requests 2026-10-25 |
| **V2-D02** | Bridge mechanism (`home_widget` vs fully native)? | **Fully native.** No `home_widget` dependency. Taps: `RemoteViews` `PendingIntent` broadcast → `BroadcastReceiver` → Kotlin `HttpURLConnection` POST. App→widget state push: small `MethodChannel` (`widget_bridge.dart`) that writes the latest `WidgetState` JSON into a private widget SharedPreferences file and calls `AppWidgetManager.notifyAppWidgetViewDataChanged`. | User delegated choice to agent ("hackathon MVP"). Native = zero new packages, no background Dart engine for taps, thin honest states; `home_widget` 0.10.0 still requires the same native RemoteViews code plus a spawned engine per tap |
| **V2-D03** | Token access path + fallback when absent? | **Direct native read/decrypt.** Kotlin re-implements flutter_secure_storage 11.2.0 format (see evidence §5): read `FlutterSecureStorage.xml`, unwrap AES key from `FlutterSecureKeyStorage` via RSA-OAEP Keystore alias `ai.hwga.hwga.FlutterSecureStoragePluginKeyOAEP`, AES/GCM decrypt. **Recorded fallback:** on any decrypt/read failure OR missing key → widget renders auth-required state deep-linking to `hwga://auth`; separately, `widget_bridge.dart` mirrors the token into a private widget prefs file on each app resume, and the native reader prefers the direct decrypt but may consume the mirror if present. | Probe 1 passed — real ciphertext observed on A142, all key material in-process readable |
| **V2-D04** | Base-URL handoff + cold-install fallback? | **`BuildConfig` field.** Gradle populates `BuildConfig.HWGA_API_BASE_URL` from the same build-time value as the dart-define; it is compiled in, so it works even when the widget is added before the app is ever opened (the only mechanism that does). **Fallback:** if the field is blank/missing, widget renders an "open the app once" state — never guesses a URL. `widget_bridge.dart` may also push a runtime URL to widget prefs on resume; native prefers it when present. | MethodChannel/home_widget-store handoffs all require ≥1 app open — rejected as primary |
| **V2-D05** | Refresh model? | **Tap-result + app-resume push + `updatePeriodMillis="1800000"`** (platform floor, Android 15). No workers, no FCM, no exact alarms. Stale UI between refreshes is accepted; hook line carries server `generated_at`. | Platform floor verified; matches TRD §5 |
| **V2-D06** | `internal/run` exposure path, regenerate semantics + cooldown? | **New user-facing route** `POST /generate/{receipt\|directive\|weekly}` locked in `contracts_v2.md` §2. Regenerate = unconditional rebuild of current period ("data so far"), replaces stored artifact for same period key, clears stale flag. Cooldown 60 s per kind per user → `429 GENERATION_COOLDOWN` (new V2 error code, contracts §4). `/internal/run/{daily\|weekly}` unchanged, stays internal. | Approved by user at V2A lock |

## 2. Phase Status Ledger

| Phase | Name | Status | Tests | Completion date | Git commit | Next |
|---|---|---|---|---|---|---|
| **V2A** | Decisions & contracts | [x] Completed | Docs + read-only probes only | 2026-10-25 | `e5166db` | V2B |
| **V2B** | Backend widget surface | [x] Completed | 104 passed (pytest, disposable DB 55533) + live curl 401/200 | 2026-10-25 | `e56b63f` | V2C |
| **V2C** | Quick-taps widget | [x] Completed | 104 pytest + 40 flutter test + on-device tap/offline/reconnect proof | 2026-10-25 | `63151f7` | V2D |
| **V2D** | Mode + today hook widget | [ ] Planned | | | | V2E |
| **V2E** | Pipeline surface & on-demand | [ ] Planned | | | | V2F |
| **V2F** | V2 acceptance | [ ] Planned | | | | Done |

## 3. Commit Protocol

Same Two-Step Commit Protocol as V1 (status.md §3): implementation commit → real hash → `status_v2.md` ledger-sync commit → push `main`. Never amend, force-push, or invent a hash.

## 4. Environment Evidence

Inherited from V1 (all still current as of HWGA08, 2026-10-25): Python 3.13.11, uv 0.11.13, Flutter 3.41.1/Dart 3.11.0, AGP 8.11.1 + KGP 2.2.20, Gradle 8.14, Docker 29.1.2 (dev 55532 / disposable test 55533), ngrok 3.39.11, Nothing Phone 2a `000563429001789` (A142, Android 15, API 35). V2A must re-verify anything V2 depends on (token storage readability, interactivity APIs).

## 5. Phase Evidence Log

### Phase V2A: V2 Decisions, Platform Probes & Contract Lock
- **Status:** [x] Completed
- **Execution date:** 2026-10-25, local machine timezone
- **Pre-flight:** `git branch --show-current` → `main`; `git status --short` → clean (no output).
- **Test results:** docs + read-only probes only — no code checks applicable.
- **Commands run + observed output (verbatim):**

  **Probe 1 — token readability (flutter_secure_storage 11.2.0, installed source + on-device):**
  - `grep flutter_secure_storage flutter/pubspec.lock` → resolved version **`11.2.0`** (`sha256: d4e1fb6b…`).
  - Installed source `~/.pub-cache/hosted/pub.dev/flutter_secure_storage-11.2.0/android/…/FlutterSecureStorageConfig.java`: `DEFAULT_PREF_NAME = "FlutterSecureStorage"`, `DEFAULT_KEY_PREFIX = "VGhpcyBpcyB0aGUgcHJlZml4IGZvciBhIHNlY3VyZSBzdG9yYWdlCg"`, `DEFAULT_STORAGE_CIPHER_ALGORITHM = "AES_GCM_NoPadding"`, `DEFAULT_KEY_CIPHER_ALGORITHM = "RSA_ECB_OAEPwithSHA_256andMGF1Padding"`. **Not EncryptedSharedPreferences** — plain SharedPreferences holding ciphertext.
  - `ciphers/StorageCipherImplementationGCM.java`: AES key 16 bytes, `AES/GCM/NoPadding`, IV 12 bytes prepended to payload, tag 128 bit; wrapped key stored under `AESVGhpcyBpcyB0aGUga2V5IGZvciBhIHNlY3VyZSBzdG9yYWdlIEFFUyBLZXkK` in `FlutterSecureKeyStorage` prefs.
  - `ciphers/KeyCipherImplementationRSAOAEP.java:41`: `keyAlias = context.getPackageName() + ".FlutterSecureStoragePluginKeyOAEP" + config.getKeyAliasSuffix()` → alias **`ai.hwga.hwga.FlutterSecureStoragePluginKeyOAEP`** (no namespace configured).
  - On-device (`adb shell run-as ai.hwga.hwga ls shared_prefs/`):
    ```
    FlutterSecureKeyStorage.xml
    FlutterSecureStorage.xml
    FlutterSecureStorageConfiguration:FlutterSecureStorage.xml
    flutter_image_picker_shared_preference.xml
    ```
  - `cat FlutterSecureStorage.xml` → real entry present:
    ```xml
    <string name="VGhpcyBpcyB0aGUgcHJlZml4IGZvciBhIHNlY3VyZSBzdG9yYWdlCg_hwga_auth_token">C9sv0FMNm4yawOSX19rZsnoaOW9ergRg4sHvPgVEuI56J2DxS0PzOI+kPHp/5smOiWkNSEztEJXJ
    tKZbtjcG/MYwtR6U100=</string>
    ```
  - **Conclusion:** ciphertext + wrapped key + Keystore alias all reachable in-process under the same UID → direct native decrypt feasible. Recorded fallback (V2-D03) covers any failure.

  **Probe 2 — bridge options:**
  - `home_widget` latest stable = **0.10.0** (pub.dev, published ~37 days before 2026-10-25 — satisfies ≥7-day rule). Verified API surface (dartdoc, v0.10.0): `saveWidgetData`, `getWidgetData`, `updateWidget`, `registerInteractivityCallback`/`registerBackgroundCallback` (background Dart callback on tap), `widgetClicked`, `initiallyLaunchedFromHomeWidget`, `getInstalledWidgets`, `requestPinWidget`. Interactivity path still requires native RemoteViews code plus a spawned Dart engine per tap → rejected for MVP (V2-D02).
  - Flutter default `minSdkVersion = 24` (`flutter_tools/gradle/.../FlutterExtension.kt:26`) — no constraint hit.

  **Probe 3 — base-URL handoff:**
  - `lib/core/config/app_config.dart` (V1 verified): `HWGA_API_BASE_URL` is compile-time `String.fromEnvironment` — invisible to Gradle/native at runtime. MethodChannel or widget-prefs handoff all require ≥1 app open. `BuildConfig` field is the only cold-install-safe mechanism → V2-D04.

  **Probe 4 — update cadence:**
  - `adb shell getprop ro.build.version.release / ro.build.version.sdk` → `15` / `35`.
  - `updatePeriodMillis` minimum is platform-enforced at 30 min (documented Android behavior); interactive RemoteViews buttons via `PendingIntent` are standard. Decision recorded as V2-D05.

- **Findings / deliverables:**
  - V2-D02…V2-D06 recorded and user-approved (D02–D05 delegated to agent for "hackathon MVP" context; D06 explicitly chosen: new user-facing route).
  - `contracts_v2.md` → **LOCKED**: `WidgetState`, `PipelineStatusItem`, `GET /widget/state`, `GET /pipeline/status`, `POST /generate/{kind}` semantics + `GENERATION_COOLDOWN` 429, deep-link table, error codes.
- **Limitations / unresolved:** none blocking V2B. Note: the `&#10;` newline artifact inside stored ciphertext strings is Android's prefs-XML escaping, handled by `getString()`/Base64 decode-with-whitespace — V2C implementation must trim/decode accordingly.

### Phase V2B: Backend Widget Surface (`GET /widget/state`)
- **Status:** [x] Completed
- **Execution date:** 2026-10-25, local machine timezone
- **Pre-flight:** `git branch --show-current` → `main`; `git status --short` → clean (no output).
- **Deliverables:**
  - `backend/app/schemas/contracts.py` — `WidgetState` added verbatim per `contracts_v2.md` §1 (V2 section marked; V1 models untouched).
  - `backend/app/services/widget_state.py` — `WidgetStateService.build(user)`: pure read; reuses `local_day_window`, `EventRepository.list_between`, `ModeService.current` (V1 open-interval `duration_min` derivation), `GoalRepository.list_for_user` + `_age_days` (V1 goal aging), `RecapRepository.get_for_period` (stored status + `stale` flag), `DirectiveRepository.get_for_date`. Missing receipt → `PENDING` + `receipt_stale=false`; unlogged confirmation kinds omitted; `directive_line` collapsed to one line, truncated ≤120 chars. Never generates.
  - `backend/app/api/routers/widget.py` — `GET /widget/state`, `require_auth` + `get_session`, `DomainError` → `HTTPException` pattern matching V1 routers; wired in `app/main.py`.
  - `backend/tests/test_widget_state.py` — 7 tests: 401 `UNAUTHORIZED`, empty-state defaults, logged-kinds-only confirmations + day-window isolation, mode + goals (age_days reuse, retired excluded), directive sanitization/truncation, stored receipt status/stale passthrough, side-effect-free (RecapRow/MorningDirectiveRow counts unchanged across a fetch).
- **Test results (verbatim):**
  - `docker compose up -d db-test` → `Container backend-db-test-1  Running`.
  - `uv run pytest tests -q -ra` → **`104 passed, 1 warning in 4.74s`** (sole warning: upstream `LangChainPendingDeprecationWarning`, pre-existing).
- **Live curl evidence (dev DB on 55532, real provisioned token):**
  - Incident recorded honestly: first `uvicorn` attempt hit `[Errno 10048]` — a stale V1-era uvicorn (PID 4516) still owned `127.0.0.1:8000`; killed via `taskkill //PID 4516 //F`, server restarted.
  - `curl http://127.0.0.1:8000/widget/state` (no token) → **HTTP 401** `{"code":"UNAUTHORIZED","message":"Missing or invalid credentials","details":{}}`.
  - `curl -H "Authorization: Bearer <token>" http://127.0.0.1:8000/widget/state` → **HTTP 200**:
    ```json
    {"generated_at":"2026-10-25T01:17:15.582008Z","mode":{"mode":"LOCKED_IN","started_at":"2026-10-25T00:12:45.008266Z","ended_at":null,"duration_min":64},"today_confirmations":{"WATER":2,"FOOD_CLEAN":3,"STRETCH":1,"POSTURE_RESET":1,"WALK":2},"quiet_moments_today":10,"goals_active":3,"oldest_goal_age_days":0,"directive_line":"A fresh page — notice one small thing worth keeping today.","directive_status":"FALLBACK","receipt_status":"GENERATED","receipt_stale":false}
    ```
    (Real V1 acceptance data in dev DB; shape matches `contracts_v2.md` §2 normative example exactly.)
- **Discrepancies found:** none — docs, live code, and installed APIs agreed at every checked point.
- **Limitations / unresolved:** none. Dev uvicorn left running on 8000 after the live check.

### Phase V2C: Quick-Taps Widget (fully native, V2-D02)
- **Status:** [x] Completed
- **Execution date:** 2026-10-25, local machine timezone
- **Pre-flight:** `git branch --show-current` → `main`; `git status --short` → clean; `adb devices` → `000563429001789 device` (A142).
- **Deliverables:**
  - `widget/QuickTapsWidgetProvider.kt` — AppWidgetProvider; `onUpdate` renders cached `WidgetState` then refreshes via `GET /widget/state` on a `goAsync` thread; `ACTION_QUICK_TAP` broadcast (exact `PendingIntent` each button sends) → `POST /events` with a fresh `UUID.randomUUID()` `idempotency_key` per tap; honest status line (`Sending…` / `Saved` / `Failed (HTTP n)` / `Not sent — no connection`); auth-required and "open the app once" states per V2-D03/D04.
  - `widget/WidgetStore.kt` — direct flutter_secure_storage 11.2.0 decrypt (Keystore RSA-OAEP alias `ai.hwga.hwga.FlutterSecureStoragePluginKeyOAEP`, AES/GCM/NoPadding, 12-byte IV, whitespace-stripped Base64 per the `&#10;` note) preferred over the app-pushed mirror; `BuildConfig.HWGA_API_BASE_URL` base-URL fallback.
  - `widget/WidgetApi.kt` — HttpURLConnection GET/POST, 10 s timeouts, typed Ok/HttpError/NetworkError.
  - `res/layout/widget_quick_taps.xml` + `res/xml/quick_taps_widget_info.xml` — RemoteViews-safe layout (LinearLayout/TextView/Button only), `updatePeriodMillis="1800000"`.
  - `AndroidManifest.xml` — exported receiver + `APPWIDGET_UPDATE` filter; `hwga` scheme VIEW filter on MainActivity. No new permissions.
  - `MainActivity.kt` — `ai.hwga.hwga/widget` MethodChannel (`sync` → mirror prefs + widget refresh; `getLaunchUri` → cold-start deep-link URI); `onNewIntent` keeps latest deep-link.
  - `build.gradle.kts` — `buildConfigField HWGA_API_BASE_URL` from env var, default `http://127.0.0.1:8000` (the D15 adb-reverse route).
  - `lib/core/widget_bridge.dart` — pushes token mirror + base URL + `/widget/state` JSON on attach and `AppLifecycleState.resumed`; best-effort (all failures swallowed — widgets have their own honest fallbacks).
  - `lib/core/api/api_client.dart` — `getWidgetState()`; `lib/main.dart` — bridge wiring sharing the app's ApiClient/TokenStore.
  - `ConnectionScreen` — `hwga://auth` cold launch with no saved token auto-opens TokenScreen (contracts_v2.md §3 auth row); generic route dispatch remains V2D scope.
  - `test/widget_bridge_test.dart` — 5 tests: mirror push with token+state, no-token honest sync, backend-error resilience, `hwga://auth` routing both ways.
- **Test results (verbatim):**
  - `dart format --set-exit-if-changed lib test` → clean after format pass; `flutter analyze` → `No issues found!`; `flutter test` → `+40: All tests passed!`
  - `uv run pytest tests -q -ra` (disposable DB 55533) → **`104 passed, 1 warning in 5.46s`** (pre-existing LangChain warning).
- **Device evidence (A142, real backend on 127.0.0.1:8000 via `adb reverse`):**
  - `flutter build apk --debug --dart-define=HWGA_DEV_TOKEN=<fresh provision-token>` installed; app reinstall had wiped the V1 secure-storage token (expected per runbook §5), so a new token was provisioned via `uv run python -m app.cli provision-token` — never committed.
  - After app launch: `hwga_widget_prefs.xml` observed with `base_url`, `token_mirror`, and full live `widget_state_json` (WATER:2…WALK:2, quiet:10) — bridge push + native mirror read verified.
  - **Tap → event:** `am broadcast ACTION_QUICK_TAP --es tap_label WATER` → `/timeline` WATER count 2 → 3; cached `widget_state_json` refreshed to `WATER:3`.
  - **Offline honesty:** `adb reverse --remove tcp:8000` → STRETCH tap → STRETCH stayed 1 (nothing queued, nothing phantom-posted).
  - **Reconnect exactly-once:** reverse restored → one STRETCH tap → total 2; new event key `ebeb0a7a-…` fresh UUID (prior key `confirm-179288…` V1-era format).
  - **Real widget instance:** launcher bound widget id 4 (`AppWidgetServiceImpl: Bound widget 4 … QuickTapsWidgetProvider`); screenshot verified all six buttons with live counts (WATER 3, FOOD 4, STRETCH 2, POSTURE 1, WALK 2, QUIET 11) and "as of 06:56" freshness line; QUIET broadcast → `quiet_moments_today` 10 → 11.
  - logcat: no `AndroidRuntime`/RemoteViews inflation errors during any update or tap.
- **Discrepancies found:** none — contracts, resolved deps, and installed APIs agreed.
- **Limitations / unresolved:**
  - Button taps were driven via `am broadcast` of the exact `ACTION_QUICK_TAP` intent the button `PendingIntent` sends (same receiver path); physical finger-tap on the pinned widget is indistinguishable at that level. Nothing OS lacks `cmd appwidget`, so pinning was done by hand on the launcher.
  - `hwga://auth` warm-start re-delivery reaches Dart only for the latest launch intent; full deep-link route table dispatch is V2D (manifest filter already registered).

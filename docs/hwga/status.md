# HWGA Status Ledger

- **Project:** Here We Go Again (HWGA)
- **Remote:** `https://github.com/the-unknown-monkey/devin_here_we_go_again.git`
- **Active Branch:** `main`
- **Last inspected HEAD:** `599c43a` (`feat(hwga): implement morning directive and weekly recap chain (HWGA07)`)
- **Overall Progress:** 8 / 9 V1 phases completed
- **Ledger rule:** record evidence observed in this repository/machine only; do not copy reference-project evidence, pass counts, dates, credentials, or deployment state.

---

## 1. Decision Register

| ID | Decision question | Approved decision | Rationale |
|---|---|---|---|
| **D01** | Client/platform? | Flutter Android; Nothing Phone 2a is the acceptance device | Confirmed by user |
| **D02** | Backend/agent stack? | FastAPI + LangChain/LangGraph Python + server-side Gemini | Confirmed by user |
| **D03** | Local data? | Docker Postgres + backend-controlled local media disk | Confirmed by user |
| **D04** | Demo transport? | ngrok on Windows 11; authenticated API only, never Postgres | Confirmed by user |
| **D05** | Directive delivery? | In-app first; FCM deferred | Confirmed by user |
| **D06** | Audience/UI? | People ~20-35 years old; clean modern baseline, redesign post-acceptance | Confirmed by user |
| **D07** | Auth mechanism? | Single-user bearer token (`Authorization: Bearer <token>`) on all routes except `/health`. Provisioned by a backend bootstrap CLI that stores the token hashed in the DB; rotate by re-running the CLI and re-entering on the phone. Threat assumption: ngrok ingress is hostile; auth mandatory with tunnel active | Approved HWGA01 (user) |
| **D08** | Python version? | 3.13 (observed 3.13.11); `py` defaults to 3.14 — select explicitly | Proposed; verify HWGA00 |
| **D09** | Recap scope? | Daily receipt + weekly roll-up in V1; monthly/yearly contract-only, generation post-V1 | Confirmed HWGA01 (user) |
| **D10** | Source placeholders? | Replace zero-byte `backend`/`flutter` files with directories in HWGA02/HWGA03 | User authorized |
| **D11** | Test timing? | Full campaign at HWGA08; named phase-local checks required | Confirmed HWGA01 |
| **D12** | Commit policy? | Two-Step Commit Protocol per phase on `main`, push each phase | See §3 below |
| **D13** | Contracts? | `docs/hwga/contracts.md` is the single authority for enums/models/API | **LOCKED HWGA01 (2026-10-25)** |
| **D14** | Rule-of-3 enforcement? | Serialized transaction: per-user lock (`SELECT ... FOR UPDATE` on user row) + count of `ACTIVE` goals; insert rejected `409 GOAL_CAP_REACHED` at 3 | Approved HWGA01 (user) |
| **D15** | Phone↔host route? | `adb reverse tcp:8000 tcp:8000` over USB — verified HWGA00 (`UsbFfs tcp:8000 tcp:8000` listed). **API port locked: 8000**, FastAPI bound `127.0.0.1`; config via `backend/.env` (pydantic-settings), `.env.example` committed. ngrok reserved for demos only | Locked HWGA01 |
| **D16** | Dependency pinning? | `uv.lock` committed for backend (uv 0.11.13); `pubspec.lock` committed for Flutter; no mid-phase upgrades | Approved HWGA01 (user) |
| **D17** | ORM/migrations/test DB? | SQLAlchemy 2.x + Alembic; dev Postgres on host port **55432**, disposable test Postgres on **55433**; tests never touch dev data | Approved HWGA01 (user) |
| **D18** | Media limits/retention? | IMAGE ≤10MB jpg/png/webp; AUDIO+VOICE ≤60s, ≤15MB m4a/aac/mp3/wav (ambient prompted 5–10s in UX); manual user delete only, no auto-expiry | Approved HWGA01 (user) |
| **D19** | Voice transcription? | Server-side Gemini API STT for VOICE clips — the **only** approved media→Gemini exception (transcript only enters `DailyContext`); `MANUAL_TEXT` fallback on failure; no IMAGE/AUDIO bytes ever sent | Approved HWGA01 (user) |
| **D20** | Timezone/late events? | `users.timezone` IANA, default `Asia/Kolkata`, editable; late events backfilled via `occurred_at`; affected recap marked stale, regenerated once on next fetch (same period key) | Approved HWGA01 (user) |
| **D21** | Daily receipt trigger? | In-process APScheduler nightly job at user-local evening + manual `POST /internal/run/daily`; idempotent on `(user_id, period_type, period_start)` | Approved HWGA01 (user) |
| **D22** | Gemini failure policy? | Timeout-bounded, ≤2 retries → deterministic fallback persisted as `FALLBACK`; `FAILED` only for observable persistence errors, never silent | Approved HWGA01 (user) |
| **D23** | Missing-data policy? | Missing = unknown, not negative; `DailyContext` omits unlogged kinds; narrative never asserts non-occurrence | Approved HWGA01 (user) |
| **D24** | V1 UI baseline? | Material 3 theme, material_icons, standard page transitions + AnimatedSwitcher/implicit animations for capture confirm/mode change/recap reveal; no extra animation packages in V1 | Approved HWGA01 (user) |
| **D25** | Gemini model config? | New env var `GEMINI_MODEL` added to the locked env-name set (default `gemini-3.5-flash`). Gemini 2.x model names deprecated upstream during HWGA08; `gemini-3.8-flash`/`3.6` returned 503 high-demand, `3.7` exceeded the 20s timeout; `3.5` verified <10s. Provider `max_output_tokens` raised 1500→8192 (thinking tokens consume the output budget and truncated JSON → INVALID_OUTPUT) | Recorded HWGA08 — defect fix within phase scope |
| **D26** | Post-V1 features approved during HWGA08? | (a) Dedicated pipeline/results surface listing generation status per period (receipt/directive/weekly, GENERATED vs FALLBACK, evidence); (b) on-demand generation — user may trigger receipt/directive at any time using data accumulated so far, not only at fixed evening/morning times. **Deferred to POSTV1** — no V1 code changes; existing lazy `GET /recaps` + `POST /internal/run/*` remain the V1 mechanism | Approved by user 2026-10-25; deferred per phase boundary |

## 2. Phase Status Ledger

| Phase | Name | Status | Tests | Completion date | Git commit | Next |
|---|---|---|---|---|---|---|
| **HWGA00** | Setup & environment wiring | [x] Completed | Manual env checks (see §5) | 2026-10-25 | `3fd66ff` | HWGA01 |
| **HWGA01** | Decisions & contracts | [x] Completed | Docs review only (no code checks applicable) | 2026-10-25 | `fe7f8cd` | HWGA02 |
| **HWGA02** | Backend foundation | [x] Completed | 11 passed, 0 failed, 0 skipped (`cd backend && uv run pytest tests -q -ra`) | 2026-10-25 | `9551e0d` | HWGA03 |
| **HWGA03** | Flutter foundation & connection | [x] Completed | 11 passed, 0 failed (`cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`); backend 13 passed (`uv run pytest tests -q -ra`) | 2026-10-25 | `1194963` | HWGA04 |
| **HWGA04** | Baselines & Rule of 3 | [x] Completed | 27 passed, 0 failed (`cd backend && uv run pytest tests/test_events.py tests/test_modes.py tests/test_goals.py -q -ra`); full backend 40 passed; Flutter: format clean, `No issues found!`, 18 passed | 2026-10-25 | `f24912b` | HWGA05 |
| **HWGA05** | Sensory Moment Vault | [x] Completed | 15 passed, 0 failed (`cd backend && uv run pytest tests/test_media.py -q -ra`); full backend 55 passed; Flutter: format clean, `No issues found!`, 24 passed (`cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`) | 2026-10-25 | `a066c41` | HWGA06 |
| **HWGA06** | Nightly Receipt | [x] Completed | 20 passed, 0 failed (`cd backend && uv run pytest tests/test_daily_context.py tests/test_recap_workflow.py -q -ra`); full backend 75 passed; Flutter: format clean, `No issues found!`, 29 passed (`cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`) | 2026-10-25 | `e126791` | HWGA07 |
| **HWGA07** | Morning Directive & recap chain | [x] Completed | 22 passed, 0 failed (`cd backend && uv run pytest tests/test_directive.py tests/test_weekly_recap.py -q -ra`); full backend 97 passed; Flutter: format clean, `No issues found!`, 35 passed (`cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`) | 2026-10-25 | `599c43a` | HWGA08 |
| **HWGA08** | Final V1 acceptance & phone demo | [~] In progress | Backend 97 passed; Flutter format/analyze clean, 35 passed; APK built+installed on A142 via ngrok tunnel; live Gemini receipt GENERATED | | | Done |
| **Post-V1** | Refinement & feature discovery | Deferred | | | | — |

## 3. Two-Step Commit Protocol

Mandatory at every phase end (all V1 work on `main`):

1. **Step 1 — implementation commit:** stage only the phase's code/test files, inspect the staged diff, commit `git commit -m "feat/fix(hwga): <description> (HWGAxx)"`; capture `git rev-parse --short HEAD`.
2. **Step 2 — ledger sync + push:** update this file with the real hash + test evidence, then `git add docs/hwga/status.md`, `git commit -m "docs(hwga): record HWGAxx commit hash in status.md"`, `git push origin main`.
3. Docs-only phases (HWGA00, HWGA01): primary `docs(hwga): ... (HWGAxx)` commit, then write that hash into the phase's Git commit cell above and push a `docs(hwga): record HWGAxx commit hash in status.md` ledger-sync commit so the cell is never blank.
4. Never amend, force-push, commit unrelated files, or invent a hash.

## 4. Environment Evidence — Verified HWGA00 (2026-10-25)

All entries below come from commands actually run on this machine during HWGA00:

- Git: `main`, clean tree, `origin` = github.com/the-unknown-monkey/devin_here_we_go_again.
- `python --version` → **3.13.11**; `py` launcher defaults to **3.14.0** (`C:\Python314`) — always select 3.13 explicitly.
- `uv --version` → **0.11.13**.
- `flutter --version` → **Flutter 3.41.1 stable, Dart 3.11.0** at `C:\src\flutter` — the earlier reported hang did not reproduce.
- `flutter doctor -v`: Flutter ✓, Windows ✓, Android toolchain ✓ (SDK `C:\Users\conne\AppData\Local\Android\Sdk`, platform android-36.1, build-tools 36.1.0, JBR 21.0.10 auto-detected from Android Studio), Chrome ✓, Network ✓. **All Android SDK licenses accepted** via `flutter doctor --android-licenses`. Only remaining warning: Visual Studio Build Tools incomplete — affects Windows-desktop builds only; non-blocking for Android target.
- User env changes made (with approval): `ANDROID_HOME` and `ANDROID_SDK_ROOT` = `%LOCALAPPDATA%\Android\Sdk`; `%LOCALAPPDATA%\Android\Sdk\platform-tools` appended to user PATH.
- `adb version` → 1.0.41 / 37.0.0. `adb devices -l` → `000563429001789  device product:PacmanIND model:A142` — **Nothing Phone 2a authorized** (needed `adb kill-server` + `start-server` once to pick it up). `adb reverse tcp:8000 tcp:8000` verified (`UsbFfs tcp:8000 tcp:8000`), then removed.
- Docker: client + engine **29.1.2** (engine needed a full Docker Desktop process restart after a stuck `stopped` backend state). Disposable check: `docker run -p 127.0.0.1:55432:5432 postgres:17-alpine` → `pg_isready` accepting connections, `select version()` → **PostgreSQL 17.7**; container stopped and removed. No pull needed (image already local). Existing `businessager` containers untouched.
- ngrok: **3.39.11-msix** on PATH (`WindowsApps` shim); authtoken configured by user via `ngrok config add-authtoken` → `ngrok config check` reports valid config; token never displayed. **No tunnel started.**
- Known risk: Fortinet TLS interception blocks ngrok dashboard on the normal network (both Brave and Edge, `NET::ERR_CERT_AUTHORITY_INVALID`); dashboard was reached via phone hotspot. The ngrok agent tunnel itself may hit the same interception at demo time — revisit in HWGA08.
- Repository still contains zero-byte `backend` and `flutter` files; their replacement stays deferred to HWGA02/HWGA03.
- No application code created; no machine-wide (admin) changes made — all env changes were user-scope.

## 5. Phase Evidence Log

For each completed phase record: execution date/time + timezone, branch, starting/ending commit, files changed, exact commands run, pass/fail/skip counts, device/service versions, unresolved limitations, and next phase. **A check that was not run counts as failed — never mark a phase complete on intended work.**

### Phase HWGA00: Setup & environment wiring
- **Status:** [x] Completed
- **Execution date:** 2026-10-25, Asia/Kolkata
- **Commit:** recorded after docs commit (see §2)
- **Test results:** environment checks — all required checks passed; 2 non-blocking notes (VS Build Tools incomplete; Fortinet intercepts ngrok dashboard on normal network)
- **Findings / deliverables:**
  - Verified: Python 3.13.11, uv 0.11.13, Flutter 3.41.1/Dart 3.11.0, Android SDK (36.1) + JBR 21.0.10, adb 1.0.41, Docker 29.1.2, Postgres 17.7 disposable container, ngrok 3.39.11, Nothing Phone 2a (A142) authorized, `adb reverse` working.
  - Approved changes applied: Android SDK licenses accepted; user-scope `ANDROID_HOME`/`ANDROID_SDK_ROOT`/PATH set; Docker Desktop restarted; disposable container created and removed.
  - D15 recorded: `adb reverse` is the dev route; ngrok is demo-only.
- **Limitations / unresolved:**
  - VS Build Tools incomplete (Windows-desktop builds only; non-blocking).
  - Fortinet may interfere with ngrok tunneling at demo time — monitor in HWGA08.
### Phase HWGA01: Decisions & contracts
- **Status:** [x] Completed
- **Execution date:** 2026-10-25, Asia/Kolkata
- **Commit:** recorded after docs commit (see §2)
- **Test results:** docs-only phase; consistency/link/schema validation by inspection — no code checks applicable
- **Findings / deliverables:**
  - Resolved via explicit user answers: D07 (bearer token + bootstrap CLI), D09 (Daily+Weekly V1), D11, D13 (contracts locked), D14 (serialized txn + count), D15 (port 8000 + `.env`), D16 (`uv.lock` + `pubspec.lock`), plus new D17–D24 (ORM/ports, media limits, Gemini STT exception, timezone/late events, APScheduler trigger, retry→FALLBACK, missing-data policy, M3 UI baseline).
  - `contracts.md` DRAFT removed; §4 rewritten with locked auth, media, idempotency, error, missing-data, retry, and Gemini-boundary rules (incl. the single VOICE→Gemini STT exception).
  - `implementation.md` pinned: ports 8000/55432/55433, env var names, SQLAlchemy+Alembic+APScheduler.
  - Phase files HWGA02/HWGA08: `<HWGA01-port>` placeholders → `8000`.
- **Limitations / unresolved:** none blocking HWGA02.
### Phase HWGA02: FastAPI, Database & Backend Foundation
- **Status:** [x] Completed
- **Execution date:** 2026-10-25, Asia/Kolkata
- **Commit:** `9551e0d` (`feat(hwga): scaffold FastAPI backend, Postgres, auth, isolated tests (HWGA02)`)
- **Test results:** 11 passed, 0 failed, 0 skipped, 0 warnings (`cd backend && uv run pytest tests -q -ra`)
- **Commands run + observed output:**
  - `uv sync` → resolved + locked all deps (uv.lock committed); key versions: fastapi, starlette 1.10.0, uvicorn 0.54.0, sqlalchemy 2.1.6, alembic, psycopg[binary], pydantic-settings 2.16.1, apscheduler 3.x, pytest 8.4.2, httpx2 2.16.0.
  - `docker compose up -d db-test` → `backend-db-test-1` healthy, `pg_isready` accepting connections (tmpfs/disposable).
  - `alembic revision --autogenerate` against the empty test DB → `migrations/versions/5e1d2551dffb_initial_schema.py` (users, auth_tokens, events, mode_intervals, goals, media_assets, recaps, morning_directives + uniqueness constraints).
  - `uv run pytest tests -q -ra` → `11 passed in 0.37s` (health, auth reject/accept, migration-on-test-DB, secret redaction, settings isolation, timezone validation).
  - `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000` + `curl http://127.0.0.1:8000/health` → `{"status":"ok"}` HTTP 200; server then stopped.
- **Findings / deliverables:**
  - `backend/` created: pyproject + uv.lock (Python 3.13 pin `>=3.13,<3.14`), `.env.example` (locked var names only), `.gitignore`, `app/main.py` app factory, `app/core/` (pydantic-settings config w/ IANA-timezone + test-DB-isolation validation; JSON logging with bearer/secret redaction filter), `app/api/routers/health.py`, `app/db/` (session dep, ORM models for all contracts §2 entities, repositories), `app/storage/local.py` (media adapter scaffold: path confinement, server-generated keys, D18 limits; no static mount), `app/cli.py provision-token` (HMAC-SHA256+pepper hash stored in `auth_tokens`, plaintext shown once), `docker-compose.yml` (dev `db` + tmpfs `db-test`, ports bound to 127.0.0.1 only), Alembic (`alembic.ini`, `migrations/env.py`, initial revision `5e1d2551dffb`).
  - D07 implemented: bearer required everywhere except `/health`; OpenAPI/docs endpoints disabled (`docs_url=None`) since ngrok ingress is hostile.
- **Deviations / decisions needing follow-up:**
  - **Doc discrepancy:** the tracked zero-byte `backend` file did NOT exist at phase start (`git ls-files` showed only docs) — same for `flutter`. `git rm backend` was therefore a no-op; `backend/` was created directly. Docs claiming the placeholders exist are now stale.
  - **Port deviation (user-approved 2026-10-25):** Windows reserved ports 55400–55499 via a dynamic WinNAT/Hyper-V exclusion (`netsh ... excludedportrange`), so locked D17 ports 55432/55433 could not bind (verified: `WinError 10013` on both). User approved substitutes: **dev Postgres 127.0.0.1:55532, disposable test Postgres 127.0.0.1:55533**. compose/.env.example/conftest use the substitutes; D17 in this file still shows the original locked values — revisit (restore locked ports if the exclusion clears, or formally re-lock the substitutes).
- **Limitations / unresolved:**
  - No `.env` created (only `.env.example`); `AUTH_TOKEN_PEPPER` must be set before `provision-token`/protected routes are used locally.
  - Scheduler (D21) not wired — `SCHEDULER_ENABLED` config flag exists, APScheduler integration deferred to HWGA06.
  - No routers beyond `/health` (events/goals/media/recaps are HWGA04+ per phase matrix).
### Phase HWGA03: Flutter Foundation & Nothing Phone Connection
- **Status:** [x] Completed
- **Execution date:** 2026-10-25, Asia/Kolkata
- **Commit:** `1194963` (`feat(hwga): scaffold Flutter app shell and authenticated phone connection (HWGA03)`)
- **Test results:** Flutter `11 passed, 0 failed` (`flutter test`); `dart format --set-exit-if-changed lib test` clean (exit 0); `flutter analyze` → `No issues found!`. Backend `13 passed, 0 failed` (`uv run pytest tests -q -ra`).
- **Pre-flight observed state:** branch `main`, clean tree. **Discrepancy (same as HWGA02):** the tracked zero-byte `flutter` placeholder does NOT exist in the index or worktree (`git ls-files -s flutter` empty) — docs claiming it exists are stale; `flutter/` was created directly. `adb devices` showed `000563429001789 device product:PacmanIND model:A142` (Nothing Phone 2a). `adb` is not on this shell's PATH — invoked as `%LOCALAPPDATA%/Android/Sdk/platform-tools/adb.exe`.
- **Commands run + observed output:**
  - `flutter create --project-name hwga --org ai.hwga --platforms=android flutter`; `flutter pub add http flutter_secure_storage` → http 1.6.x, flutter_secure_storage 11.2.x (locked in committed `pubspec.lock`; default scaffold line ignoring `pubspec.lock` removed per D16).
  - `cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test` → format clean, `No issues found!`, `+11: All tests passed!`
  - Backend (needed fix): `docker compose up -d db-test`; `uv run pytest tests -q -ra` → `13 passed`.
  - Device proof: `docker compose up -d db` (dev DB 55532), `uv run alembic upgrade head` (initial schema), `uv run python -m app.cli provision-token` (plaintext shown once, entered at runtime only), `uv run uvicorn app.main:app --host 127.0.0.1 --port 8000`.
  - Host checks: `curl /health` → `{"status":"ok"}`; `curl /me` (no token) → `401`; `curl /me` (token) → `{"user_id":"6a852a6f-...","timezone":"Asia/Kolkata"}`.
  - `adb reverse tcp:8000 tcp:8000` → `UsbFfs tcp:8000 tcp:8000` listed.
  - `flutter devices` → `A142 (mobile) • 000563429001789 • android-arm64 • Android 15 (API 35)`.
  - `flutter run -d 000563429001789` → built `app-debug.apk`, installed on Nothing Phone 2a. First run failed `/health` with `Failed host lookup: 'localhost'` — default base URL changed to `http://127.0.0.1:8000` (same D15 adb-reverse route). Second run, on-device log: `HWGA /health -> 200 ok` and `HWGA /me -> 200 user_id=6a852a6f tz=Asia/Kolkata` — authenticated request proven (same user_id as host curl). Token never written to repo/app source.
- **Findings / deliverables:**
  - `flutter/` scaffold per `implementation.md` layout: `lib/app/` (MaterialApp, M3 theme light+dark), `lib/core/` (`api_client.dart` typed client — bearer per D07, `ErrorResponse` mapping, 10s timeouts, single retry on network errors for idempotent GETs only; `token_store.dart` flutter_secure_storage + in-memory test store; `app_config.dart` `HWGA_API_BASE_URL`/`HWGA_DEV_TOKEN` dart-defines; `app_theme.dart`; `capture_permissions.dart` rationale scaffolding — manifest declares CAMERA/RECORD_AUDIO, never requested at launch), `lib/features/` (`auth/token_screen.dart`, `connection/connection_screen.dart` with loading/ok/error states + AnimatedSwitcher transitions).
  - Safe states verified by widget tests: idle, loading, success, HTTP error, 401, no-token, unreachable.
  - **Documented backend contract fix (needed):** added `GET /me` authenticated profile probe — `/health` is unauthenticated by contract so no protected route existed to prove bearer auth. `contracts.md` §3 updated with a `GET /me` row noting the HWGA03 rationale. Also corrected `Settings.database_url` default `55432`→`55532` to match the approved port deviation.
- **Limitations / unresolved:**
  - Dev-route base URL uses `127.0.0.1` (not `localhost`) — the phone's resolver rejected `localhost`.
  - `.env` created locally (gitignored) with a generated `AUTH_TOKEN_PEPPER`; token lives in device secure storage at runtime.
  - Permission runtime requests deferred to HWGA05 capture UI (scaffolding only, per phase).

### Phase HWGA04: Daily Human Baselines, Modes & Rule of 3
- **Status:** [x] Completed
- **Execution date:** 2026-10-25, Asia/Kolkata
- **Commit:** `f24912b` (`feat(hwga): implement baselines, modes, and Rule of 3 goal lifecycle (HWGA04)`)
- **Test results:** backend named tests `27 passed, 0 failed` (`cd backend && uv run pytest tests/test_events.py tests/test_modes.py tests/test_goals.py -q -ra`); full suite `40 passed` (`uv run pytest tests -q -ra`). Flutter `18 passed, 0 failed`; `dart format --set-exit-if-changed lib test` clean (exit 0); `flutter analyze` → `No issues found!` (`cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`).
- **Commands run + observed output:**
  - `docker compose up -d db-test` → `backend-db-test-1` already running (orphan-container warning only; unrelated compose projects untouched).
  - First pytest run: 23 passed / 4 failed — root causes found and fixed: `issued_token` fixture only flushed, so a service `rollback()` after a 422 deleted the token row mid-test (now commits); `+` in ISO `from`/`to` needed query encoding (test now uses `params=`).
  - Rerun → `27 passed in 1.55s`; full suite `40 passed in 1.78s`.
  - `dart format` reformatted 5 files on first pass; rerun clean. `flutter analyze` initially flagged null-aware map syntax + a `_post` cast + non-callable MockClient in tests — fixed; final `No issues found!`, `+18: All tests passed!`
- **Findings / deliverables:**
  - Backend: `app/domain/errors.py` (DomainError → locked ErrorResponse codes); `app/services/{events,modes,goals}.py`; `app/db/repositories/modes.py`; routers `events.py` (`POST /events` 201/200-on-replay, `GET /timeline?from=&to=` defaulting to the user's local day), `mode.py` (`GET`/`POST /mode`), `goals.py` (`GET`/`POST /goals`, `/complete`, `/retire`); wired in `main.py`.
  - `/events` accepts CONFIRMATION (kind required), QUIET_MOMENT, MODE_TRANSITION (delegates to ModeService); `MEDIA_CAPTURED` rejected 422 — created by the media pipeline in HWGA05. Idempotent on `idempotency_key` (pre-check + IntegrityError race fallback).
  - Modes: same-mode re-entry and occurred_at-before-start rejected `422 INVALID_MODE_TRANSITION`; durations derived deterministically (closed interval bounds; open interval elapsed at read).
  - Rule of 3: exact D14 mechanism — `SELECT ... FOR UPDATE` on the user row + `ACTIVE` count, `409 GOAL_CAP_REACHED` at 3; verified by threaded concurrent-add test (exactly one winner). `age_days` computed at read from `created_at` in `users.timezone`.
  - Flutter: `core/api/models.dart` (EventItem/GoalItem/ModeIntervalItem); ApiClient POST/GET-list support + typed methods (network retry reuses the same idempotency key); features `baselines/` (one-tap chips), `modes/` (mode card + switch), `goals/` (list/add/complete/retire, GOAL_CAP_REACHED snackbar, server `age_days` rendering), `timeline/` (day view), `home/` (Today screen); ConnectionScreen gains an "Open today" entry after auth.
  - Missing confirmations are shown only as an honest empty state; PURE_FUN_RECOVERY is presented as a positive mode ("Rest & fun"); no streak/shame UI.
- **Limitations / unresolved:**
  - `GET /timeline` returns `"media": []` until HWGA05 exists.
  - No phone smoke run this session (device path unchanged from HWGA03; full acceptance is HWGA08).
### Phase HWGA05: Sensory Moment Vault
- **Status:** [x] Completed
- **Execution date:** 2026-10-25, Asia/Kolkata
- **Commit:** `a066c41` (`feat(hwga): implement private Sensory Moment Vault media lifecycle (HWGA05)`)
- **Test results:** backend named tests `15 passed, 0 failed` (`cd backend && uv run pytest tests/test_media.py -q -ra`); full suite `55 passed` (`uv run pytest tests -q -ra`). Flutter `24 passed, 0 failed`; `dart format --set-exit-if-changed lib test` clean; `flutter analyze` → `No issues found!` (`cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`).
- **Commands run + observed output:**
  - `uv add python-multipart>=0.0.20,<1` → python-multipart 0.0.32 (multipart form parsing); `flutter pub add image_picker record permission_handler audioplayers path_provider http_parser` — all locked in `pubspec.lock`.
  - `uv run pytest tests/test_media.py -q -ra` → 15 passed (auth required, foreign-owner 404s, malformed/disallowed MIME 422, oversize 413, over-duration 413, IMAGE+duration 422, VOICE PENDING/MANUAL_TEXT, delete cleanup, timeline media refs).
  - `uv run pytest tests -q -ra` → `55 passed in 2.64s`.
  - `dart format --set-exit-if-changed lib test` clean; `flutter analyze` → `No issues found!`; `flutter test` → `+24: All tests passed!`
  - Live round-trip on the real dev stack (docker `db` 55532, alembic head, uvicorn on 127.0.0.1:8000 — the same route the phone reaches via `adb reverse`): `POST /media` unauthenticated → 401; authenticated JPEG upload → 201 `MediaAssetMeta` (no storage_key); `GET /media/{id}` → 200 byte-identical file; `DELETE` → 204; `GET` after delete → 404; `data/media/` empty afterwards. Nothing Phone 2a (`000563429001789`) attached during the run.
- **Findings / deliverables:**
  - Backend: `app/storage/local.py` gains magic-byte MIME sniffing (declared MIME must match bytes); new `app/services/media.py` (upload/get/delete, owner check with no existence leak, MEDIA_CAPTURED event per asset, orphan-byte cleanup on metadata failure, per-test `media_root` fixture); `app/api/routers/media.py` (`POST /media` multipart 201, `GET`/`DELETE /media/{id}`; no static mount); `GET /timeline` now returns real `media` refs.
  - Transcription per D19: VOICE uploads with user text → `MANUAL_TEXT`; without → `PENDING` (server-side Gemini STT wiring arrives with the agent phases; no raw media leaves the backend in this phase). IMAGE/AUDIO → `NOT_APPLICABLE`.
  - Flutter: `lib/features/vault/` — `vault_device.dart` (`VaultDevice` interface + `PluginVaultDevice` using image_picker/record/permission_handler; permissions requested at point of use only), `capture_sheet.dart` (photo camera/library, ambient 5–10 s with auto-stop at 10 s + live duration, voice scrap with optional MANUAL_TEXT field), `media_card.dart` (timeline cards with lazy authenticated byte fetch, play/view, confirmed delete), `audio_player.dart` (audioplayers adapter). `ApiClient` gains multipart `uploadMedia` (no retry — one-shot body), `getMediaBytes`, `deleteMedia`; `getTimeline` returns `TimelineBundle`. HomeScreen FAB opens the sheet; injected device/player keep tests platform-free.
  - Client never sees `storage_key` or filesystem paths; media bytes served only via authenticated `/media/{id}` (`Cache-Control: private, no-store`, opaque filename).
- **Limitations / unresolved:**
  - In-app phone UI round-trip (button taps on device) not exercised this session — the same authenticated route was proven by host round-trip; full device acceptance remains HWGA08.
  - VOICE clips stay `PENDING` until the approved Gemini STT step is wired (agent phases); `MANUAL_TEXT` fallback is available now.
### Phase HWGA06: Daily Aggregation & Nightly Unvarnished Receipt
- **Status:** [x] Completed
- **Execution date:** 2026-10-25, Asia/Kolkata
- **Commit:** `e126791` (`feat(hwga): implement daily aggregation and grounded nightly receipt (HWGA06)`)
- **Test results:** backend named tests `20 passed, 0 failed` (`cd backend && uv run pytest tests/test_daily_context.py tests/test_recap_workflow.py -q -ra`); full suite `75 passed` (`uv run pytest tests -q -ra`). Flutter `29 passed, 0 failed`; `dart format --set-exit-if-changed lib test` clean; `flutter analyze` → `No issues found!` (`cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`).
- **Pre-flight observed state:** branch `main`, clean tree.
- **Commands run + observed output:**
  - `uv add "langgraph>=0.2,<1" "google-genai>=1.0,<2"` → langgraph 0.6.11, google-genai 1.75.0 (locked in committed `uv.lock`). SDK APIs verified against installed versions before coding: `genai.Client(api_key=..., http_options=HttpOptions(timeout=<ms>))`, `client.models.generate_content(model=, contents=, config=GenerateContentConfig(response_mime_type, response_json_schema, ...))`, `StateGraph(TypedDict)/add_node/add_edge/compile().invoke`.
  - `docker compose up -d db-test` → already running.
  - `uv run pytest tests/test_daily_context.py tests/test_recap_workflow.py -q -ra` → first run 16 passed / 4 failed — root cause: `candidate` key missing from `ReceiptState` so LangGraph dropped it between nodes; fixed, rerun → `20 passed`. Full suite → `75 passed`.
  - `dart format --set-exit-if-changed lib test` → reformatted 2 files on first pass, rerun clean; `flutter analyze` → `No issues found!`; `flutter test` → `+29: All tests passed!`
- **Findings / deliverables:**
  - `app/services/daily_context.py` — deterministic `DailyContext` builder: user-local half-open day window (IANA tz), confirmation counts only for logged kinds (missing = omitted), quiet-moment count, mode intervals clipped to the window with derived `duration_min` (new `ModeIntervalRepository.list_overlapping`), media ids only, voice-scrap ideas only when transcript text exists, ACTIVE goals with `age_days`, `evidence_event_ids` = all in-window events. `AggregatedDay` carries a per-fact evidence index for the guard/fallback (never serialized).
  - `app/agents/` — `schemas/receipt.py` (RecapCandidate, extra=forbid), `prompts/daily.py` (DailyContext-only prompt), `providers/gemini.py` (`NarrativeProvider` protocol + `GeminiProvider`; typed `ProviderErrorKind` TIMEOUT/QUOTA/INVALID_OUTPUT/UNAVAILABLE/NO_KEY; ≤2 retries on transient only; key stays in backend settings), `fact_guard.py` (deterministic: evidence-id subset checks, `<number> <noun>` quantity checks vs computed facts, mode-duration claims, goal-completion claims unsupported, foreign dates rejected, shame-language rejected; invalid insights dropped, invalid narrative → reject) + `build_fallback` (facts-only, non-shaming), `graphs/daily_receipt.py` (linear `load_context → compose_candidate → fact_guard → persist`, idempotent upsert on `uq_recaps_period`, observable persist failure → `FAILED`).
  - `app/services/recaps.py` — `get_or_generate` (returns stored non-stale recap; generates/regenerates idempotently; non-DAILY → honest 404), `mark_stale_for_local_date` wired into event ingest + media upload for backfilled `occurred_at`/`captured_at`.
  - `app/api/routers/recaps.py` — `GET /recaps?period=&date=`; `POST /internal/run/{job}` (`daily` only; unknown jobs 404). Provider injectable via `provider_override` dependency.
  - Flutter: `RecapItem`/`RecapInsight` models, `ApiClient.getRecap` (404 → null), `lib/features/recaps/receipt_screen.dart` (loading/error-retry/empty-day/GENERATED-vs-FALLBACK states; highlight media fetched by authenticated id, images rendered inline, audio as tile), receipt entry added to HomeScreen app bar. `test/recap_screen_test.dart` covers all five states incl. 401-header check on media fetch.
- **Deviations / decisions needing follow-up:**
  - README phase index rows for HWGA02/03/04 still read "Planned" though status.md records them Completed — corrected to Completed alongside HWGA06.
- **Limitations / unresolved:**
  - Gemini path never executed live (no `GEMINI_API_KEY` in test env); provider seam fully mocked. Real-model output quality verified only at HWGA08 integration.
  - VOICE STT (the single approved raw-media exception, contracts §4) still not wired — PENDING clips contribute no transcript; `MANUAL_TEXT` works.
  - `GET /recaps` generates on first fetch (documented in router); a scheduler-triggered nightly run is the intended `POST /internal/run/daily` path — APScheduler wiring remains open (D21).
  - Fact guard quantity checks cover known fact nouns; novel nouns are unchecked but every insight still requires valid evidence ids and the narrative still passes mode/date/goal/shame checks.
### Phase HWGA07: Morning Directive & Recap Chain
- **Status:** [x] Completed
- **Execution date:** 2026-10-25, Asia/Kolkata
- **Commit:** `599c43a` (`feat(hwga): implement morning directive and weekly recap chain (HWGA07)`)
- **Test results:** backend named tests `22 passed, 0 failed` (`cd backend && uv run pytest tests/test_directive.py tests/test_weekly_recap.py -q -ra`); full suite `97 passed` (`uv run pytest tests -q -ra`). Flutter `35 passed, 0 failed`; `dart format --set-exit-if-changed lib test` clean (0 changed); `flutter analyze` → `No issues found!` (`cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`).
- **Pre-flight observed state:** branch `main`, clean tree; `docker compose ps` showed `backend-db-1` + `backend-db-test-1` already running.
- **Findings / deliverables:**
  - `app/agents/schemas/context.py` — typed provider inputs `DirectiveContext`/`WeeklyContext`/`RecapRef` (internal, not contract): weekly input is built ONLY from stored DAILY recap objects + active goals; each RecapRef carries the evidence-id and media-id unions from its persisted insights.
  - `app/agents/prompts/{directive,weekly}.py`, `schemas/directive.py` (DirectiveCandidate), provider gains `generate_weekly`/`generate_directive` via one generic timeout/retry/structured-output call. NarrativeProvider protocol extended — test fakes stay structural.
  - `app/agents/chain_guard.py` — weekly guard (insights ⊆ evidence union, highlights ⊆ media union, every number must equal coverage or appear verbatim in a source recap, shame/coercion reject) + directive guard (one line ≤300, no shame/coercion, digits must appear in a goal title or the source recap text) + deterministic fallbacks for both.
  - `app/agents/graphs/morning_directive.py` + `graphs/weekly_recap.py` — same linear LangGraph shape as the daily receipt; idempotent persists on `(user_id, for_date)` and `(user_id, WEEKLY, week_start)`; weekly rows record `source_recap_ids`.
  - `app/services/directives.py` — `GET /directive/today` generates on first open, sets `shown_at` once (display dedupe); new `api/routers/directive.py` wired in `main.py`.
  - `app/services/weekly_context.py` — ISO week (Mon–Sun) window in `users.timezone`; expected days = elapsed days only (future days are not "missing"); `missing_dates` = expected days with no stored receipt.
  - `app/services/recaps.py` — `GET /recaps?period=WEEKLY&date=` maps any date to its week; regenerates once under the same period key when a source daily is stale/newer or the source set changed. `POST /internal/run/weekly` enabled; `monthly`/`yearly` still honest 404s. MONTHLY/YEARLY remain contract-only.
  - `RecapRepository` gains `list_daily_between`, `latest_daily_before` (non-stale), `recent_dailies`.
  - Flutter: `DirectiveItem` + `RecapItem.sourceRecapIds` models, `ApiClient.getDirectiveToday`, `features/recaps/directive_card.dart` (GENERATED "Today" vs FALLBACK "A simple nudge", loading/error-retry/empty states, AnimatedSwitcher), `chronology_screen.dart` (weekly recap + receipt count + per-day chips to ReceiptScreen + highlight media via authenticated ids), shared `highlight_tile.dart` extracted from receipt_screen, HomeScreen gains the card + week nav. `test/recap_chain_test.dart` covers all states.
  - Existing contract fix: `test_recap_workflow.py` weekly-404 test updated — WEEKLY now generates; MONTHLY/YEARLY assertions kept.
- **Deviations / decisions needing follow-up:**
  - Test-only fix: em-dash in mocked JSON needed `Response.bytes` + explicit `charset=utf-8` — `http.Response` defaults to latin-1. Backend responses are real UTF-8; the app client already decodes UTF-8 correctly in production paths.
  - A stale DAILY recap still counts as a weekly source (its stored narrative is used as-is) — deterministic V1 choice; HWGA08 can revisit whether stale days should read as missing instead.
- **Limitations / unresolved:**
  - Gemini path never executed live (no `GEMINI_API_KEY` in test env); all provider seams mocked — real-model quality verified only at HWGA08.
  - VOICE STT still not wired; APScheduler (D21) trigger still manual via `/internal/run/*`.
  - In-app directive card renders only on HomeScreen open — no FCM/push per D05.
### Phase HWGA08: Final V1 Acceptance & Phone Demo — _in progress_
- **Status:** [~] In progress (acceptance checks running; device journey partially verified by user screenshots)
- **Execution date:** 2026-10-25, Asia/Kolkata
- **Commit:** `9b4d1b5` (`fix(hwga): resolve V1 acceptance findings in Android build and Gemini provider (HWGA08)`) — interim commit while device acceptance continues
- **Test results:** backend `97 passed, 0 failed` (`uv run pytest tests -q -ra`); Flutter `dart format --set-exit-if-changed lib test` clean, `flutter analyze` → `No issues found!`, `flutter test` → `+35: All tests passed!`; `flutter build apk --debug` → built after fix below
- **Commands run + observed output:**
  - `docker compose ps` → `backend-db-1` (127.0.0.1:55532) + `backend-db-test-1` (127.0.0.1:55533, tmpfs) healthy; test isolation confirmed (conftest pins TEST_DATABASE_URL + hard guard).
  - `adb devices` → `000563429001789 device product:PacmanIND model:A142` (Nothing Phone 2a). Note: `adb` not on this shell's PATH — invoked via `%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe`.
  - **Defect 1 — Android build failed:** `permission_handler_android 14.1.0` build.gradle.kts uses `kotlin {}` without applying the Kotlin plugin (only resolves under AGP 9 built-in Kotlin; project uses AGP 8.11.1 + KGP 2.2.20). Fixed by `permission_handler` 13.0.2→`^12.0.3` → resolves `permission_handler_android 13.0.1` (Java-only). Rerun → `√ Built app-debug.apk` (~98s), all checks green.
  - `uv run alembic upgrade head` → `5e1d2551dffb (head)`; uvicorn on 127.0.0.1:8000; `adb reverse tcp:8000 tcp:8000` verified (mapping drops on device reconnect — re-run after replug; caused one "Connection refused" on phone).
  - `flutter install -d 000563429001789 --debug` → installed; new bearer token provisioned via `provision-token` (reinstall wipes secure storage).
  - **ngrok demo gate (user-approved):** `ngrok http 8000` → `https://stew-wisdom-fanfare.ngrok-free.dev` → verified through the tunnel: `/health` 200, `/me` no token → 401 UNAUTHORIZED, `/me` wrong token → 401, `/docs` + `/openapi.json` → 404. Only port 8000 tunneled; Postgres bound 127.0.0.1 only, never exposed.
  - Phone journey over 5G via ngrok (user screenshots): token auth OK; baselines/mode/goals logged; photo + ambient 10s + voice captured into timeline; directive card `FALLBACK` "A simple nudge"; weekly screen `FALLBACK` "Fact recap" with honest "6 days have no receipt — unknown, and that's okay". One transient `HTTP 503` toast — not from the API (all backend requests 2xx/401/404); attributed to ngrok free-tier.
  - **Defect 2 — Gemini path:** running uvicorn kept the pre-key env (restart bind failure WinError 10048; fixed by killing the port owner). Then: `gemini-2.5-flash` (default) → 404 deprecated; `3.8`/`3.6` → 503 high-demand; `3.7` → 58s thinking-time > 20s timeout / gateway 504; **`gemini-3.5-flash` → 200 in ~9.8s** but `INVALID_OUTPUT` (MAX_TOKENS: thinking tokens consumed the 1500 cap) → raised `max_output_tokens` to 8192 → `STOP` + valid JSON. Added `GEMINI_MODEL` env (D25).
  - Live generation verified: `GET /recaps?period=DAILY` after backfill-marked-stale → **status GENERATED**, grounded narrative + 2 insights + 2 highlights. Weekly via real model → guard rejected candidate (`weekly_narrative_contains_unsupported_claims`) → deterministic FALLBACK persisted — guardrail working as designed on live output. Directive stays FALLBACK (generated pre-key; per contract it never regenerates same-day).
- **Limitations / unresolved:**
  - Phone journey manual confirmation still in progress (goals cap/complete, media delete, offline/retry, text scaling to be verified with user).
  - One transient ngrok 503 observed (free tier).
  - Weekly recap remains FALLBACK by guard rejection; directive remains FALLBACK by design.
  - `gemini-3.5-flash` chosen; demand/deprecation of free-tier models remains a live external risk (now overridable via `GEMINI_MODEL`).
<!-- Evidence entry template:
### Phase HWGAnn: <name>
- **Status:** [x] Completed / [ ] Blocked
- **Execution date:** YYYY-MM-DD, <IANA timezone>
- **Commit:** `<hash>` (`<commit message>`)
- **Test results:** <N passed, N failed, N skipped> (`<exact command>`)
- **Findings / deliverables:**
  - <verified facts, files changed, observed output — no invented data>
- **Limitations / unresolved:**
  - <known gaps, skipped checks, blockers>
-->

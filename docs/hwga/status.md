# HWGA Status Ledger

- **Project:** Here We Go Again (HWGA)
- **Remote:** `https://github.com/the-unknown-monkey/devin_here_we_go_again.git`
- **Active Branch:** `main`
- **Last inspected HEAD:** `1194963` (`feat(hwga): scaffold Flutter app shell and authenticated phone connection (HWGA03)`)
- **Overall Progress:** 4 / 9 V1 phases completed
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

## 2. Phase Status Ledger

| Phase | Name | Status | Tests | Completion date | Git commit | Next |
|---|---|---|---|---|---|---|
| **HWGA00** | Setup & environment wiring | [x] Completed | Manual env checks (see §5) | 2026-10-25 | `3fd66ff` | HWGA01 |
| **HWGA01** | Decisions & contracts | [x] Completed | Docs review only (no code checks applicable) | 2026-10-25 | `fe7f8cd` | HWGA02 |
| **HWGA02** | Backend foundation | [x] Completed | 11 passed, 0 failed, 0 skipped (`cd backend && uv run pytest tests -q -ra`) | 2026-10-25 | `9551e0d` | HWGA03 |
| **HWGA03** | Flutter foundation & connection | [x] Completed | 11 passed, 0 failed (`cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test`); backend 13 passed (`uv run pytest tests -q -ra`) | 2026-10-25 | `1194963` | HWGA04 |
| **HWGA04** | Baselines & Rule of 3 | [ ] Planned | | | | HWGA05 |
| **HWGA05** | Sensory Moment Vault | [ ] Planned | | | | HWGA06 |
| **HWGA06** | Nightly Receipt | [ ] Planned | | | | HWGA07 |
| **HWGA07** | Morning Directive & recap chain | [ ] Planned | | | | HWGA08 |
| **HWGA08** | Final V1 acceptance & phone demo | [ ] Planned | | | | Done |
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
- **Pre-flight observed state:** branch `main`, clean tree. **Discrepancy (same as HWGA02):** the tracked zero-byte `flutter` placeholder does NOT exist in the index or worktree (`git ls-files -s flutter` empty) — docs claiming it exists are stale; `flutter/` was created directly. `adb devices` showed `000563429001789 device product:PacmanIND model:A142` (Nothing Phone 2a). `adb` is not on this shell's PATH — invoked as `%LOCALAPPDATA%\Android\Sdk\platform-toolsdb.exe`.
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

### Phase HWGA04 — _pending_
### Phase HWGA05 — _pending_
### Phase HWGA06 — _pending_
### Phase HWGA07 — _pending_
### Phase HWGA08 — _pending_

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

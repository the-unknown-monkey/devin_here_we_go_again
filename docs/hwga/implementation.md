# HWGA Implementation Map & Environment Baseline

- **Document ID:** IMPL-HWGA
- **Scope:** Flutter Android client, FastAPI backend, LangChain/LangGraph workflows, local Postgres, local media store, ngrok demo
- **Authoritative phase:** [HWGA00 Setup & Environment Wiring](phases/HWGA00_environment_setup_and_wiring.md)

---

## 1. Repository and Git Baseline

| Item | Observed value |
|---|---|
| Repository root | `C:\Users\conne\Desktop\devin_here_we_go_again` |
| Remote `origin` | `https://github.com/the-unknown-monkey/devin_here_we_go_again.git` |
| Branch at audit | `main` |
| HEAD at audit | `6b5be03` (`new docs`) |
| Working tree at audit | Clean |
| `backend` | Tracked zero-byte file; not yet a directory |
| `flutter` | Tracked zero-byte file; not yet a directory |
| Existing product document | `here_we_go_again.md` |

HWGA02 is explicitly authorized to replace the two zero-byte placeholders with source directories. Do not do this during HWGA00 or documentation work.

## 2. Planned Source Layout

The following is an intended layout, not a claim that these files already exist. **It is illustrative:** create only what each phase needs, and always inspect the real tree before importing or referencing paths — never assume a file exists because it is drawn here. Adjust names only after inspecting generated framework files and recording the decision in `status.md`.

```text
backend/
  pyproject.toml
  .env.example
  Dockerfile
  app/
    main.py
    api/routers/
    core/                 # settings, auth, logging
    db/                   # session, migrations, repositories
    domain/               # events, modes, goals, recap rules
    services/             # application use cases
    storage/              # private local media adapter
    agents/
      graphs/
      prompts/
      schemas/
      providers/          # Gemini adapter and fallback
    scheduler/
  tests/
  migrations/
  data/media/             # runtime-only; ignored by git
  docker-compose.yml       # local Postgres only; do not publish DB port publicly

flutter/
  pubspec.yaml
  lib/
    main.dart
    app/
    core/                 # API client, config, theme, errors
    features/
      auth/
      timeline/
      baselines/
      modes/
      goals/
      vault/
      recaps/
  test/
```

Flutter may generate platform-specific Android project files. Keep secrets and user media out of source control; commit only a safe `.env.example`.

## 3. Environment Audit (Observed, Not Yet Phase-00 Accepted)

Machine context: Windows 11 (25H2, build 26200); Nothing Phone 2a is the target device. **Verified in HWGA00 (2026-10-25)** — values below are from real command output:

| Component | Verified value | HWGA00 outcome |
|---|---|---|
| Git | 2.52.0.windows.1 | `main`, clean tree, `origin` correct |
| Python | `python` → 3.13.11 | `py` launcher defaults to 3.14.0 (`C:\Python314`) — select 3.13 explicitly, never bare `py` |
| `uv` | 0.11.13 | Use for repeatable Python environment if selected in HWGA01 |
| Flutter/Dart | Flutter 3.41.1 stable, Dart 3.11.0 at `C:\src\flutter` | `flutter doctor -v` passes Android toolchain; earlier `--version` hang did not reproduce |
| Android Studio | `C:\Program Files\Android\Android Studio` | Bundled JBR auto-detected by Flutter |
| Android SDK | `C:\Users\conne\AppData\Local\Android\Sdk`; platforms 35/36/36.1; build-tools 35.0.0/36.1.0/37.0.0 | `ANDROID_HOME`+`ANDROID_SDK_ROOT` set (user scope); all SDK licenses accepted |
| Android device tooling | adb 1.0.41 (37.0.0) in platform-tools | platform-tools added to user PATH; Nothing Phone 2a (serial `000563429001789`, `model:A142`, `product:PacmanIND`) shows `device`; `adb reverse` verified |
| Emulator | Emulator 36.5.11.0 binary present | No AVD; not needed — physical phone path chosen |
| Java | Android Studio JBR `OpenJDK 21.0.10` | No system `java`/`JAVA_HOME`; Flutter auto-uses bundled JBR |
| Docker | Client + engine 29.1.2 (Docker Desktop) | Engine verified; disposable `postgres:17-alpine` → PostgreSQL 17.7, `pg_isready` OK, stopped+removed |
| ngrok | 3.39.11-msix on PATH | Authtoken stored locally (`ngrok config check` valid); no tunnel started. Fortinet TLS interception on normal network blocks dashboard — hotspot used; monitor at demo |
| PostgreSQL CLI | `psql` on host not needed | Container `docker exec ... psql` workflow verified |
| Gemini credential | Not inspected | Configure in backend env only when needed; never paste into chat |

Approved user-scope changes made in HWGA00: Android SDK licenses accepted; `ANDROID_HOME`, `ANDROID_SDK_ROOT`, and platform-tools PATH entry set; Docker Desktop restarted (a stuck `stopped` backend required killing and relaunching Docker Desktop processes). No machine-wide/admin changes; no project packages installed.

## 4. Setup Verification Commands (PowerShell)

Run in HWGA00 and record actual outputs. Commands that download, install, change environment variables, or require admin rights need user approval before execution.

```powershell
git status --short
git branch --show-current
git remote -v
python --version
uv --version
flutter --version
flutter doctor -v
adb version
adb devices
docker version
docker info
ngrok version
```

Minimum readiness criteria:

- Flutter doctor recognizes Flutter, Android SDK, Android Studio/JDK, and an Android target.
- Nothing Phone 2a appears as `device` in `adb devices`, not `unauthorized` or `offline`.
- `python` resolves to the agreed Python 3.13 interpreter.
- Docker client and engine both respond; disposable Postgres can start and pass a health query.
- ngrok agent version is recorded; token is configured without printing it; no tunnel is started until API authentication is available.
- The test DB and app DB are distinct; integration tests never point at a user's working dataset.

## 5. Local Runtime and Data Boundaries

- **Locked (HWGA01):** FastAPI binds `127.0.0.1:8000`; the phone reaches it via `adb reverse tcp:8000 tcp:8000`. Config comes from `backend/.env` (pydantic-settings); only `.env.example` is committed.
- Run Postgres in Docker with a named volume for local development on host port **55432**, and a separate disposable test database/container on host port **55433** (locked HWGA01); tests never point at the dev DB.
- **Locked environment variable names** (names only — values never committed): `DATABASE_URL`, `TEST_DATABASE_URL`, `MEDIA_STORAGE_ROOT`, `GEMINI_API_KEY`, `USER_TIMEZONE` (default `Asia/Kolkata`), `AUTH_TOKEN_PEPPER` (hashing secret for the bootstrap-CLI-issued bearer token), `SCHEDULER_ENABLED`.
- **Locked backend libraries:** SQLAlchemy 2.x + Alembic (ORM/migrations, D17), APScheduler (in-process nightly receipt job, D21), pydantic-settings; exact versions come from `uv.lock` at scaffold time (D16).
- Store media under an ignored backend-owned data root. Persist opaque relative keys and metadata, never client-supplied paths.
- The phone reaches a local server via a verified development route (USB reverse or ngrok). Do not assume `localhost` on the Android phone is the Windows host.
- Expose only the backend route through ngrok; bind database access to local-only networks.
- Gemini credentials exist only in backend environment; Flutter has no provider key.

## 6. Phase ↔ File Matrix

Phase → primary files/deliverables. Fill in exact paths as phases land; the target column is the plan, not a promise that files exist.

| Phase | Primary files & deliverables | Layer | Prerequisite |
|---|---|---|---|
| **HWGA00** | Environment verification; updates to `implementation.md`/`status.md` evidence only | Machine setup | — |
| **HWGA01** | `docs/hwga/contracts.md` locked; `status.md` decisions; `trd.md`/`implementation.md` aligned | Docs only | HWGA00 |
| **HWGA02** | `backend/` scaffold: `pyproject.toml`, `uv.lock`, `.env.example`, `app/main.py`, `app/core/`, `app/db/`, `app/storage/`, `docker-compose.yml`, `backend/tests/` | Backend | HWGA01 |
| **HWGA03** | `flutter/` scaffold: `pubspec.yaml`, `lib/main.dart`, `lib/app/`, `lib/core/api client`, `lib/features/auth/`, app shell/theme | Flutter | HWGA02 |
| **HWGA04** | `app/domain/` events/modes/goals rules, `app/api/routers/` event+mode+goal routes, `lib/features/{timeline,baselines,modes,goals}/` | Both | HWGA03 |
| **HWGA05** | `app/storage/` media adapter, media routers, `lib/features/vault/` capture + playback | Both | HWGA04 |
| **HWGA06** | `app/domain/` daily aggregation, `app/agents/{graphs,prompts,schemas,providers}/`, recap router, `lib/features/recaps/` receipt view | Both | HWGA05 |
| **HWGA07** | Directive workflow + router, weekly recap workflow, `lib/features/recaps/` directive card + chronology | Both | HWGA06 |
| **HWGA08** | `docs/hwga/runbook.md` (only after verified acceptance); no new feature code | Both | HWGA07 |

## 7. Test Harness Matrix

Exact commands get pinned when each layer exists; until then phases must not invent commands.

| Layer | Command (once scaffolded) | Target |
|---|---|---|
| Backend unit/domain | `cd backend && uv run pytest tests -q -ra` | disposable test DB only |
| Backend single file | `uv run pytest tests/<file>.py -q -ra` | disposable test DB only |
| Flutter analyze | `cd flutter && dart format --set-exit-if-changed lib test && flutter analyze` | — |
| Flutter widget tests | `flutter test` | — |
| Flutter device build | `flutter run -d <nothing-phone-id>` | Nothing Phone 2a via `adb devices` |
| Health check | `curl http://127.0.0.1:8000/health` | port locked HWGA01: 8000 |

Test isolation rules: the disposable test database/container is separate from the dev database; tests never point at a user's real dataset. Locked in HWGA01: dev Postgres on host port **55432**, disposable test Postgres on host port **55433**.

## 8. Phase-Level Test Harness vs. Final Acceptance

Every code phase uses focused checks appropriate to its scope (format, static analysis, compile, selected unit/contract tests). The **full regression and end-to-end campaign is HWGA08**, including:

- Backend unit and API tests against disposable Postgres.
- Rule-of-3 concurrency, mode/timestamp, time-zone boundary, idempotency, and media authorization/limit tests.
- Gemini success, timeout/quota, malformed-output, fact-guard, and deterministic-fallback tests using mocked providers where appropriate.
- Flutter static analysis, widget tests, Android build/install, permission-denial and offline/retry checks.
- End-to-end capture → persist → nightly receipt → next-day directive → weekly recap.
- Physical Nothing Phone 2a verification and ngrok security/demo smoke test.

Passing a phase-local check is not equivalent to final V1 acceptance.

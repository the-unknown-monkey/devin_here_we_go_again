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

Machine context: Windows 11; Nothing Phone 2a is the target device. The following observations were made during documentation planning; HWGA00 must recheck them and capture actual command output.

| Component | Observed | Remaining action |
|---|---|---|
| Git | 2.52.0.windows.1 | Verify `git status`, branch, and `origin` at phase start |
| Python | `python` is 3.13.11 | Pin/use 3.13 for backend; `py` launcher defaults to 3.14.0, so avoid an unqualified launcher |
| `uv` | 0.11.13 | Use for repeatable Python environment if selected in HWGA01 |
| Flutter/Dart | SDK path `C:\src\flutter`; Dart SDK cache present | `flutter --version` did not complete in the initial check; run `flutter doctor -v`, record version and fix diagnostics |
| Android Studio | Installed under `C:\Program Files\Android\Android Studio` | Use bundled JBR; verify Android Studio SDK configuration |
| Android SDK | `%LOCALAPPDATA%\Android\Sdk`; platforms 35, 36, 36.1; build-tools 35.0.0, 36.1.0, 37.0.0; platform-tools, emulator, cmdline-tools present | `ANDROID_HOME` and `ANDROID_SDK_ROOT` unset; verify Flutter can locate SDK |
| Android device tooling | SDK `platform-tools/adb.exe` exists | `adb` not on PATH; connect Nothing Phone 2a, enable USB debugging, authorize this PC, verify `adb devices` |
| Emulator | Emulator binary exists | No system image/AVD found; not required for selected physical-phone path |
| Java | Android Studio bundled `jbr/bin/java.exe` exists | `java`/`JAVA_HOME` not on PATH; use Studio's bundled JBR if Flutter requires it |
| Docker | Docker CLI 29.1.2 exists | Docker engine/daemon not verified; launch Docker Desktop and verify `docker info` |
| ngrok | Not found on PATH | Install/configure only after approval; account token must remain outside docs/source |
| PostgreSQL CLI | `psql` not found | Not required if the disposable DB runs in Docker; use a container/client workflow |
| Gemini credential | Not inspected | Obtain/configure in the backend environment only when needed; never paste into chat |

No project packages were installed and no machine-wide settings were changed during the planning audit.

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

- Run FastAPI locally on a documented loopback port; HWGA01 locks the port and configuration format.
- Run Postgres in Docker with a named volume for local development and a separate disposable test database/container.
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
| Health check | `curl http://127.0.0.1:<port>/health` | port locked in HWGA01 |

Test isolation rules: the disposable test database/container is separate from the dev database; tests never point at a user's real dataset; the disposable Postgres host port is assigned in HWGA01/HWGA02 and recorded in `status.md`.

## 8. Phase-Level Test Harness vs. Final Acceptance

Every code phase uses focused checks appropriate to its scope (format, static analysis, compile, selected unit/contract tests). The **full regression and end-to-end campaign is HWGA08**, including:

- Backend unit and API tests against disposable Postgres.
- Rule-of-3 concurrency, mode/timestamp, time-zone boundary, idempotency, and media authorization/limit tests.
- Gemini success, timeout/quota, malformed-output, fact-guard, and deterministic-fallback tests using mocked providers where appropriate.
- Flutter static analysis, widget tests, Android build/install, permission-denial and offline/retry checks.
- End-to-end capture → persist → nightly receipt → next-day directive → weekly recap.
- Physical Nothing Phone 2a verification and ngrok security/demo smoke test.

Passing a phase-local check is not equivalent to final V1 acceptance.

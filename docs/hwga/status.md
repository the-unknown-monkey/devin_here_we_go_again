# HWGA Status Ledger

- **Project:** Here We Go Again (HWGA)
- **Remote:** `https://github.com/the-unknown-monkey/devin_here_we_go_again.git`
- **Active Branch:** `main`
- **Last inspected HEAD:** `6b5be03` (`new docs`)
- **Overall Progress:** 0 / 9 V1 phases completed
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
| **D07** | Auth mechanism? | Single-user private auth; exact mechanism/token/provisioning **open — lock in HWGA01** | Partially decided |
| **D08** | Python version? | 3.13 (observed 3.13.11); `py` defaults to 3.14 — select explicitly | Proposed; verify HWGA00 |
| **D09** | Recap scope? | Daily loop + weekly roll-up in V1; monthly/yearly deferred | Proposed for HWGA01 confirmation |
| **D10** | Source placeholders? | Replace zero-byte `backend`/`flutter` files with directories in HWGA02/HWGA03 | User authorized |
| **D11** | Test timing? | Full campaign at HWGA08; named phase-local checks required | Confirm interpretation HWGA01 |
| **D12** | Commit policy? | Two-Step Commit Protocol per phase on `main`, push each phase | See §3 below |
| **D13** | Contracts? | `docs/hwga/contracts.md` is the single authority for enums/models/API | Seeded; locked in HWGA01 |
| **D14** | Rule-of-3 enforcement? | **Open — HWGA01** must pick DB mechanism (e.g. partial unique index) | Prevents silent choice in HWGA04 |
| **D15** | Phone↔host route? | `adb reverse tcp:<port> tcp:<port>` over USB for development — verified working on Nothing Phone 2a (`UsbFfs tcp:8000 tcp:8000` listed). Phone reaches backend at `http://localhost:<port>`; ngrok reserved for demos only | Verified HWGA00 |
| **D16** | Dependency pinning? | **Open — HWGA01** lock strategy (`uv.lock`, `pubspec.lock`); no mid-phase upgrades | Prevents version drift hallucination |

## 2. Phase Status Ledger

| Phase | Name | Status | Tests | Completion date | Git commit | Next |
|---|---|---|---|---|---|---|
| **HWGA00** | Setup & environment wiring | [x] Completed | Manual env checks (see §5) | 2026-10-25 | `3fd66ff` | HWGA01 |
| **HWGA01** | Decisions & contracts | [ ] Planned | — | | | HWGA02 |
| **HWGA02** | Backend foundation | [ ] Planned | | | | HWGA03 |
| **HWGA03** | Flutter foundation & connection | [ ] Planned | | | | HWGA04 |
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
### Phase HWGA01 — _pending_
### Phase HWGA02 — _pending_
### Phase HWGA03 — _pending_
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

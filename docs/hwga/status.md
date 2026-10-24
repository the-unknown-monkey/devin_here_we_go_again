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
| **D15** | Phone↔host route? | **Open — HWGA00/HWGA01** record verified route (USB reverse / LAN / ngrok) | Never assume phone `localhost` |
| **D16** | Dependency pinning? | **Open — HWGA01** lock strategy (`uv.lock`, `pubspec.lock`); no mid-phase upgrades | Prevents version drift hallucination |

## 2. Phase Status Ledger

| Phase | Name | Status | Tests | Completion date | Git commit | Next |
|---|---|---|---|---|---|---|
| **HWGA00** | Setup & environment wiring | [ ] Planned | — | | | HWGA01 |
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
3. Docs-only phases (HWGA00, HWGA01) use a single `docs(hwga): ... (HWGAxx)` commit + push.
4. Never amend, force-push, commit unrelated files, or invent a hash.

## 4. Environment Evidence at Documentation Baseline

Observed paths/versions are recorded in [`implementation.md`](implementation.md). Important limitations:

- `flutter doctor -v` and a working Nothing Phone 2a ADB connection have not been verified.
- Docker CLI exists, but Docker engine readiness and disposable Postgres startup have not been verified.
- ngrok is not found on PATH; no ngrok account token has been configured.
- Android SDK files are present, but Android SDK environment variables and `adb` PATH configuration are absent.
- No application code, dependencies, migrations, test suites, or end-to-end tests have been created/run.
- Repository contains zero-byte files named `backend` and `flutter`, not source directories. Their replacement is deferred to HWGA02/HWGA03.

## 5. Phase Evidence Log

For each completed phase record: execution date/time + timezone, branch, starting/ending commit, files changed, exact commands run, pass/fail/skip counts, device/service versions, unresolved limitations, and next phase. **A check that was not run counts as failed — never mark a phase complete on intended work.**

### Phase HWGA00 — _pending_
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

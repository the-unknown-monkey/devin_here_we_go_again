# HWGA Status Ledger

- **Project:** Here We Go Again (HWGA)
- **Remote:** `https://github.com/the-unknown-monkey/devin_here_we_go_again.git`
- **Branch at baseline:** `main`
- **Last inspected HEAD:** `6b5be03` (`new docs`)
- **Last inspected worktree:** clean
- **Ledger rule:** record evidence observed in this repository/machine only; do not copy reference-project evidence.

---

## 1. Decision Register

| ID | Topic | Current decision | Status / owner |
|---|---|---|---|
| D01 | Client/platform | Flutter Android; Nothing Phone 2a is the acceptance device | Confirmed by user |
| D02 | Backend/agent | FastAPI + LangChain/LangGraph Python + Gemini server-side | Confirmed by user |
| D03 | Local data | Docker Postgres + backend-controlled local media disk | Confirmed by user |
| D04 | Demo transport | ngrok on Windows 11; API only, authentication stays required | Confirmed by user |
| D05 | Directive | In-app first; FCM deferred | Confirmed by user |
| D06 | Audience/UI | Target age group is people approximately 20-35 years old (not a user-count target); clean modern baseline with intentional transitions/icons; larger redesign after phone acceptance | Confirmed by user |
| D07 | Auth | Single-user private auth; exact mechanism, token/session design, and threat assumptions to be locked HWGA01 | Partially decided |
| D08 | Python version | Use 3.13; observed 3.13.11, while `py` defaults to 3.14.0 | Proposed, verify HWGA00 |
| D09 | Recap scope | Daily loop + weekly roll-up prioritized; monthly/yearly implementation deferred past V1 unless user changes scope | Proposed for HWGA01 confirmation |
| D10 | Source placeholders | Replace zero-byte `backend` and `flutter` files with directories in HWGA02 | User authorized for implementation phase |
| D11 | Full test timing | User requests the full V1 test campaign at final HWGA08; focused phase checks are retained as a proposed quality safeguard | Final interpretation to confirm in HWGA01 |
| D12 | Branch/commit/push | Current baseline is `main`; no branch changes or commits/pushes without explicit user direction | Current guardrail |

## 2. Phase Status

| Phase | Status | Evidence / next gate |
|---|---|---|
| HWGA00 Setup & environment wiring | Planned | Recheck toolchain; Flutter doctor, ADB phone auth, Docker engine, ngrok, isolated DB |
| HWGA01 Decisions & contracts | Planned | Resolve remaining D07/D09 and API/data/privacy contract details |
| HWGA02 Backend foundation | Planned | Implement only after HWGA01 accepted |
| HWGA03 Flutter foundation & connection | Planned | Verify authenticated Nothing Phone 2a request |
| HWGA04 Baselines & Rule of 3 | Planned | Domain and UI behavior |
| HWGA05 Sensory Moment Vault | Planned | Private media round-trip and limits |
| HWGA06 Nightly Receipt | Planned | Typed AI output, fact guard, deterministic fallback |
| HWGA07 Morning Directive & recap chain | Planned | In-app directive and agreed recap tiers |
| HWGA08 Final V1 acceptance & phone demo | Planned | Full regression, Nothing Phone 2a, ngrok; runbook only after verified completion |
| Post-V1 refinement | Deferred | Begin only after HWGA08 acceptance |

## 3. Environment Evidence at Documentation Baseline

Observed paths/versions are recorded in [`implementation.md`](implementation.md). Important limitations:

- `flutter doctor -v` and a working Nothing Phone 2a ADB connection have not been verified.
- Docker CLI exists, but Docker engine readiness and disposable Postgres startup have not been verified.
- ngrok is not found on PATH; no ngrok account token has been configured.
- Android SDK files are present, but Android SDK environment variables and `adb` PATH configuration are absent.
- No application code, dependencies, migrations, test suites, or end-to-end tests have been created/run.
- Repository contains zero-byte files named `backend` and `flutter`, not source directories. Their replacement is deferred to HWGA02.

## 4. Phase Evidence Protocol

For each phase record: date/time and timezone; branch and starting/ending commit; files changed; exact commands; pass/fail/skip counts; device/service versions; unresolved limitations; and next phase. Do not mark a phase complete based on intended work or a command that was not run.

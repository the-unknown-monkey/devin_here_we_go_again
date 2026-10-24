# Phase HWGA01: Product Decisions, Data Contracts & V1 Freeze

- **Phase ID:** HWGA01
- **Title:** Product Decisions, Data Contracts & V1 Freeze
- **Branch:** `main`
- **Status:** Completed (2 / 9 completed)
- **Dependency:** HWGA00 environment readiness
- **Next Phase:** HWGA02
- **Scope:** Confirm open requirements and lock authoritative contracts; no feature implementation

## 1. Goal

Convert the product vision into a small, testable V1 contract before application code is built. Resolve open choices explicitly, lock `docs/hwga/contracts.md`, record decisions in `status.md`, and align the product blueprint, TRD, and implementation map.

## 2. Required Reading

1. `here_we_go_again.md`
2. `docs/hwga/trd.md`
3. `docs/hwga/contracts.md` — seeded draft to finalize
4. `docs/hwga/implementation.md`
5. `docs/hwga/status.md`

## 3. Decisions to Close

- **D07 auth:** exact single-user auth mechanism and how the initial credential is provisioned/rotated; threat assumptions.
- Python environment/lock strategy (`uv.lock`) and FastAPI configuration; use verified Python 3.13 (**D16** dep pinning; `pubspec.lock` for Flutter).
- Database migration/ORM approach and separate app/test database strategy (incl. disposable test-DB port).
- **D14 Rule-of-3 enforcement mechanism:** pick the concrete DB-level guard (e.g. partial unique index on `(user_id) WHERE status='ACTIVE'` or transactional count check); do not leave to HWGA04 to improvise.
- **D15 phone↔host route:** confirm HWGA00's recorded dev route; lock API port and config format.
- Local media limits, retention, deletion, accepted MIME types, audio duration, and upload size.
- Voice transcription provider and manual-text fallback; explicitly decide whether any raw media may be sent to Gemini (default: no).
- User-local timezone source and period boundary/late-event policy.
- Daily receipt trigger/retry/idempotency and how the morning directive becomes due.
- V1 acceptance scope for weekly recap; monthly/yearly remain future tiers unless the user explicitly changes the boundary.
- Minimal V1 UI baseline and exact low-cost animations/icons; detailed polish remains post-V1.
- Review and finalize every sketch in `contracts.md` (enums, models, API routes, error envelope, idempotency format); remove DRAFT status.

## 4. Deliverables

1. Update `status.md` decision register: mark each open D-entry resolved with rationale.
2. Lock `docs/hwga/contracts.md` — the single authoritative shape for events, modes, goals, media metadata, `DailyContext`, recap, Morning Directive, API routes, error envelope, and idempotency. Include error and missing-data behavior.
3. Update `trd.md` where a locked decision changes an invariant or boundary.
4. Update `implementation.md` with selected libraries, exact source layout, local ports, environment variable names (names only), test-DB port, and test isolation.
5. Update `here_we_go_again.md` only if approved scope changes; avoid duplicate contradictory architecture.
6. Refine phase files HWGA02+ only where a locked decision changes a named file path, test command, or deliverable.

## 5. Exit Criteria

- No unresolved decision blocks database/API/schema implementation (D07, D09, D14, D15, D16 all resolved or explicitly deferred with owner).
- `contracts.md` has DRAFT removed and is the single authoritative definition; no other doc restates shapes contradictorily.
- V1 must-have vs. deferred/post-V1 scope is explicit.
- Service boundary, privacy, fallback, and final acceptance rules agree across documents.

## 6. Phase Completion & Git Protocol (Two-Step)

Docs-only phase: primary docs commit, then a ledger-sync commit so the Git commit cell is not left blank.

```powershell
git add docs/hwga/contracts.md docs/hwga/status.md docs/hwga/trd.md docs/hwga/implementation.md docs/hwga/phases
git commit -m "docs(hwga): lock V1 decisions and typed contracts (HWGA01)"
git rev-parse --short HEAD
# write that hash into the HWGA01 row's Git commit cell in status.md, then:
git add docs/hwga/status.md
git commit -m "docs(hwga): record HWGA01 commit hash in status.md"
git push origin main
```

Deliver handoff summary: **Completed 2 / 9; Remaining: 7**.

## 7. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA01: Product Decisions, Data Contracts & V1 Freeze on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short

Read docs/hwga/README.md, the complete here_we_go_again.md, docs/hwga/trd.md, docs/hwga/contracts.md, docs/hwga/implementation.md, docs/hwga/status.md, and phases/HWGA01_decisions_and_contracts.md. Inspect current Git state and actual repository files first.

This is a design/contracts phase, not feature coding. Resolve each open decision in the phase file (D07 auth, D09 recap scope, D14 Rule-of-3 DB mechanism, D15 phone route, D16 dependency locking, plus the listed config/media/timezone/idempotency choices) by asking me concise, grouped questions where needed. Do not guess or silently choose. Record my answers in status.md with rationale, then lock contracts.md (remove DRAFT) as the single authoritative source for enums, typed models, API routes, error envelope, and idempotency.

Preserve my constraints: Flutter Android on Nothing Phone 2a, FastAPI/Python 3.13, LangChain/LangGraph + server-side Gemini, Docker Postgres + local private media, single-user private use, in-app directive, ngrok only for authenticated API demo, and major UI polish only after V1 phone acceptance.

Separate deterministic calculations from Gemini narrative; define typed inputs/outputs, error states, idempotency, timezone rules, media authorization/limits, and missing-data behavior. Default to no raw media sent to Gemini. Do not invent package versions, API names, source files, or test output. If codebase evidence contradicts docs, report it before updating the contract.

Change documentation only (docs/, and phase files where a locked decision changes named files/commands). Validate links, consistency, and schemas by inspection; do not run deployment or network commands.

Finish with the docs commit: stage docs/hwga files, commit "docs(hwga): lock V1 decisions and typed contracts (HWGA01)", then write the resulting short hash into the HWGA01 Git commit cell in status.md, commit "docs(hwga): record HWGA01 commit hash in status.md", push origin main. Report both commit hashes. Report exact files/decisions changed and remaining blockers. Stop before HWGA02.
```

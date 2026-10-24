# Phase HWGA01: Product Decisions, Data Contracts & V1 Freeze

- **Status:** Planned
- **Dependency:** HWGA00 environment readiness
- **Scope:** Confirm open requirements and author authoritative contracts; no feature implementation

## 1. Goal

Convert the product vision into a small, testable V1 contract before application code is built. Resolve open choices explicitly, record decisions in `status.md`, and align the product blueprint, TRD, and implementation map.

## 2. Required Reading

1. `here_we_go_again.md`
2. `docs/hwga/trd.md`
3. `docs/hwga/implementation.md`
4. `docs/hwga/status.md`
5. Both user-provided reference pipeline document sets, for phase discipline and decision/evidence format only.

## 3. Decisions to Close

- Exact single-user auth mechanism and how the initial credential is provisioned/rotated.
- Python environment/lock strategy and FastAPI configuration; use verified Python 3.13.
- Database migration/ORM approach and separate app/test database strategy.
- Local media limits, retention, deletion, accepted MIME types, audio duration, and upload size.
- Voice transcription provider and manual-text fallback; explicitly decide whether any raw media may be sent to Gemini (default: no).
- User-local timezone source and period boundary/late-event policy.
- Daily receipt trigger/retry/idempotency and how the morning directive becomes due.
- V1 acceptance scope for weekly recap; monthly/yearly remain future tiers unless the user explicitly changes the boundary.
- Minimal V1 UI baseline and exact low-cost animations/icons; detailed polish remains post-V1.
- API port/config and device-to-host connection approach for the Nothing Phone 2a.

## 4. Deliverables

1. Update `status.md` with numbered decisions, rationale, owner, and date.
2. Update `trd.md` with the locked data/API contracts and acceptance conditions.
3. Update `implementation.md` with selected libraries, exact source layout, local ports, environment variable names (names only), and test isolation.
4. Update `here_we_go_again.md` only if approved scope changes; avoid duplicate contradictory architecture.
5. Define typed request/response shapes for events, modes, goals, media metadata, DailyContext, recap, and Morning Directive. Include error and missing-data behavior.

## 5. Exit Criteria

- No unresolved decision blocks database/API/schema implementation.
- All contracts have a single authoritative definition and deterministic field ownership.
- V1 must-have vs. deferred/post-V1 scope is explicit.
- Service boundary, privacy, fallback, and final acceptance rules agree across documents.

## 6. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA01: Product Decisions, Data Contracts & V1 Freeze.

Read docs/hwga/README.md, the complete here_we_go_again.md, docs/hwga/trd.md, docs/hwga/implementation.md, docs/hwga/status.md, and this phase file. Inspect current Git state and actual repository files first. The two reference pipeline doc sets are trusted examples for decision registers, service boundaries, deterministic-vs-LLM separation, phase contracts, and evidence; do not copy their Shopify services, cloud setup, credentials, or implementation assumptions.

This is a design/contracts phase, not feature coding. Resolve each open decision listed here by asking me concise, grouped questions where needed. Do not guess or silently choose. Record my answers in status.md with rationale, then update the authoritative contracts and scope. Preserve the user's constraints: Flutter Android on Nothing Phone 2a, FastAPI/Python 3.13, LangChain/LangGraph + server-side Gemini, Docker Postgres + local private media, single-user private use, in-app directive, ngrok only for authenticated API demo, and major UI polish only after V1 phone acceptance.

Separate deterministic calculations from Gemini narrative; define typed inputs/outputs, error states, idempotency, timezone rules, media authorization/limits, and missing-data behavior. Default to no raw media sent to Gemini. Do not invent package versions, API names, source files, or test output. If codebase evidence contradicts docs, report it before updating the contract.

Change documentation only. Validate links, consistency, and schemas by inspection; do not run deployment or network commands. Report exact files/decisions changed and remaining blockers. Do not commit/push. Stop before HWGA02.
```

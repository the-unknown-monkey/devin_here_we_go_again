# Phase HWGA04: Daily Human Baselines, Modes & Rule of 3

- **Status:** Planned
- **Dependency:** HWGA02 and HWGA03 complete; HWGA01 contracts accepted
- **Scope:** Core event capture and goal lifecycle, backend rules plus Flutter interaction

## 1. Goal

Make the daily fundamentals quick to log and impossible to misrepresent: confirmations and mode intervals are timestamped, while the backend strictly enforces the three-active-goal rule.

## 2. Deliverables

- Typed event API/service/repository for approved baseline confirmations and quiet moments.
- Mode transition API with only approved states; validate transition ordering and calculate duration deterministically.
- Goal create/list/complete/retire endpoints; enforce at most three active goals atomically under concurrent requests.
- Calculate goal age from stored creation time and user-local display timezone.
- Flutter private timeline/day view, one-tap confirmations, mode control, goal aging, and understandable full-cap message.
- Idempotency or duplicate-tap protection according to HWGA01 contract; clear offline/failure state that does not claim a save before server confirmation.

## 3. Safety and Product Rules

- A missing confirmation is **unknown**, not proof the user skipped a healthy action.
- Rest is a positive, valid mode; no shame language, streak punishment, or comparison UI.
- The backend is the authority for time, mode transition, goal cap, and persisted state.
- No LLM use in this phase.

## 4. Exit Criteria

- Focused API/domain and Flutter interaction checks cover accepted/rejected events, mode changes, active-goal cap, complete/retire slot release, and timestamp/age rendering.
- No client-only enforcement of the 3-slot cap.
- Confirm one phone smoke path without treating it as final V1 acceptance.

## 5. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA04: Daily Human Baselines, Modes & Rule of 3.

Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/implementation.md, docs/hwga/status.md, the accepted HWGA01 data/API contracts, relevant backend and Flutter files, and this phase. Inspect current branch/worktree and source before changes.

Implement only the baseline event confirmations, valid mode transition logging, private timeline interactions, and backend-enforced Rule-of-3 goal lifecycle. Use the existing service boundaries: Flutter calls typed API; router delegates; domain/application service enforces rules; repository owns SQL. Do not put time math, goal-cap authority, or persistence rules only in the UI. Do not add AI, extra health tracking, social functionality, or unapproved fields.

Missing confirmation means unknown, not failure. Rest must be represented positively and without shame. Enforce the cap transactionally to handle concurrent adds. Compute goal aging from timestamps/timezone rather than a counter. Preserve unrelated work and avoid changing files outside this phase.

Add/run focused phase-local checks for domain/API behavior and changed widgets, recording exact commands and outcomes. Full regression/phone acceptance remains HWGA08. Update status with observed evidence, failures, and caveats. No commit/push. Stop before HWGA05.
```

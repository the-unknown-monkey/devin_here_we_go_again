# Phase HWGA04: Daily Human Baselines, Modes & Rule of 3

- **Phase ID:** HWGA04
- **Title:** Daily Human Baselines, Modes & Rule of 3
- **Branch:** `main`
- **Status:** Planned (0 / 9 completed)
- **Dependency:** HWGA02 + HWGA03 complete; HWGA01 contracts accepted
- **Next Phase:** HWGA05
- **Scope:** Core event capture and goal lifecycle, backend rules plus Flutter interaction

## 1. Goal

Make the daily fundamentals quick to log and impossible to misrepresent: confirmations and mode intervals are timestamped, while the backend strictly enforces the three-active-goal rule.

## 2. Required Reading

`docs/hwga/trd.md`, `docs/hwga/contracts.md` (EventIn, GoalItem, enums, API table), `docs/hwga/implementation.md`, `docs/hwga/status.md`, and decisions D07/D14.

## 3. Deliverables

- Event API/service/repository for `EventIn` (contracts.md): `CONFIRMATION` kinds, `QUIET_MOMENT`, `MODE_TRANSITION`; idempotent on `idempotency_key`.
- Mode transition endpoints (`GET`/`POST /mode`): only `LOCKED_IN`/`PURE_FUN_RECOVERY`; validate transition ordering and derive durations deterministically.
- Goal endpoints per contracts.md (`/goals`, `/goals/{id}/complete`, `/goals/{id}/retire`); enforce ≤3 `ACTIVE` goals using the **D14 mechanism locked in HWGA01** — implement exactly that mechanism, do not improvise another.
- `age_days` computed from `created_at` + user timezone at read time; never a stored counter.
- Flutter: private timeline/day view, one-tap confirmations, mode control, goal aging display, clear `GOAL_CAP_REACHED` message.
- Duplicate-tap protection via `idempotency_key`; offline/failure state that does not claim a save before server confirmation.
- Tests: `backend/tests/test_events.py`, `test_modes.py`, `test_goals.py` (incl. concurrent-add cap case); widget tests for the new screens.

## 4. Safety and Product Rules

- A missing confirmation is **unknown**, not proof the user skipped a healthy action.
- Rest is a positive, valid mode; no shame language, streak punishment, or comparison UI.
- The backend is the authority for time, mode transition, goal cap, and persisted state.
- No LLM use in this phase.

## 5. Exit Criteria

- Named tests cover accepted/rejected events, invalid mode transitions, active-goal cap (incl. concurrent add), complete/retire slot release, and timestamp/age rendering.
- No client-only enforcement of the 3-slot cap.
- One phone smoke path confirmed (not treated as final V1 acceptance).

## 6. Test Commands

```powershell
cd backend && uv run pytest tests/test_events.py tests/test_modes.py tests/test_goals.py -q -ra
cd ..\flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test
```

## 7. Phase Completion & Git Protocol (Two-Step)

1. Run the commands above; confirm pass counts.
2. **Step 1 — implementation commit:**
   ```powershell
   git add backend flutter
   git commit -m "feat(hwga): implement baselines, modes, and Rule of 3 goal lifecycle (HWGA04)"
   git rev-parse --short HEAD
   ```
3. **Step 2 — ledger sync + push:** update `status.md`, then:
   ```powershell
   git add docs/hwga/status.md
   git commit -m "docs(hwga): record HWGA04 commit hash in status.md"
   git push origin main
   ```
4. Deliver handoff summary: **Completed 5 / 9; Remaining: 4**.

## 8. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA04: Daily Human Baselines, Modes & Rule of 3 on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short

Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/contracts.md, docs/hwga/implementation.md, docs/hwga/status.md, and phases/HWGA04_daily_baselines_and_rule_of_three.md. Inspect current backend/Flutter source before changes.

Implement only the baseline event confirmations, valid mode transition logging, private timeline interactions, and backend-enforced Rule-of-3 goal lifecycle — using contracts.md shapes exactly (EventIn, GoalItem, enums, /events /mode /goals routes, ErrorResponse codes). Enforce the 3-cap with the D14 mechanism recorded in status.md; if that decision is missing, stop and ask. Use the existing service boundaries: Flutter calls typed API; router delegates; domain service enforces rules; repository owns SQL. Do not put time math, goal-cap authority, or persistence rules only in the UI. No AI, extra health tracking, social features, or unapproved fields.

Missing confirmation means unknown, not failure. Rest is positive, no shame. Compute goal aging from timestamps/timezone, not a counter. Use idempotency_key for duplicate taps. Preserve unrelated work.

Write and run the named tests:
  cd backend && uv run pytest tests/test_events.py tests/test_modes.py tests/test_goals.py -q -ra
  cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test
Record exact commands and outcomes. A check that was not run counts as failed. Full regression/phone acceptance remains HWGA08.

Finish with the Two-Step Commit Protocol exactly as written in the phase file (implementation commit → hash → status.md docs commit → git push origin main). Report both commit hashes. Stop before HWGA05.
```

# Phase HWGA07: Morning Directive & Recap Chain

- **Phase ID:** HWGA07
- **Title:** Morning Directive & Recap Chain
- **Branch:** `main`
- **Status:** Planned (0 / 9 completed)
- **Dependency:** HWGA06 daily recap available
- **Next Phase:** HWGA08
- **Scope:** In-app directive, weekly compaction, and supported recap chronology

## 1. Goal

Use the stored daily receipt and short recent history to produce a concrete next-day action, then demonstrate hierarchical memory by generating a weekly recap from saved `DAILY` recaps rather than replaying every raw event.

## 2. Required Reading

`docs/hwga/trd.md`, `docs/hwga/contracts.md` (Recap, MorningDirective, RecapPeriod), `docs/hwga/implementation.md`, `docs/hwga/status.md`, the recap/directive contracts, and the implemented HWGA06 workflow.

## 3. Deliverables

- Deterministic selection of eligible recap/history and active goals for the user's local date.
- Typed `MorningDirective` workflow: input context → Gemini proposal → schema/fact validation → idempotent persistence (unique on `(user_id, for_date)`).
- Deterministic safe fallback directive on model/provider failure (`GenerationStatus.FALLBACK`); no FCM in V1.
- In-app directive card on first relevant app open; `shown_at` marks display without duplicate generation.
- `WEEKLY` recap workflow consuming stored `DAILY` recap objects (`source_recap_ids`), with period completeness/missing-day markers and curated `highlight_media_ids`.
- Private chronology view joining recap narratives to authenticated media references; no sharing, likes, streak comparison, or social affordance.
- `MONTHLY`/`YEARLY` lineage contracts only (already sketched in contracts.md); full generation/UI stays post-V1 unless HWGA01 explicitly approved expansion.
- Tests: `backend/tests/test_directive.py` (no recap, local date change, retry/idempotency, provider failure), `test_weekly_recap.py` (partial week, missing days, consumes recap ids not raw events); directive card widget tests.

## 4. Boundaries and Correctness

- Never tell the user something based on absent evidence as if it were a fact.
- Keep recommendations small, non-coercive, and connected to a real event or active goal.
- Weekly recap summarizes stored daily recaps; do not send all raw records to the model.
- Timezone, partial weeks, app-open retries, and generation idempotency are deterministic.

## 5. Exit Criteria

- Named tests cover no recap, missing days, partial week, retry, provider failure, local date change, and duplicate app open.
- Weekly pipeline proven to consume daily recap records and preserve source/media references.
- Directive and chronology screens handle empty and fallback states.

## 6. Test Commands

```powershell
cd backend && uv run pytest tests/test_directive.py tests/test_weekly_recap.py -q -ra
cd ..\flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test
```

## 7. Phase Completion & Git Protocol (Two-Step)

1. Run the commands above; confirm pass counts.
2. **Step 1 — implementation commit:**
   ```powershell
   git add backend flutter
   git commit -m "feat(hwga): implement morning directive and weekly recap chain (HWGA07)"
   git rev-parse --short HEAD
   ```
3. **Step 2 — ledger sync + push:** update `status.md`, then:
   ```powershell
   git add docs/hwga/status.md
   git commit -m "docs(hwga): record HWGA07 commit hash in status.md"
   git push origin main
   ```
4. Deliver handoff summary: **Completed 8 / 9; Remaining: 1**.

## 8. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA07: Morning Directive & Recap Chain on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short

Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/contracts.md, docs/hwga/implementation.md, docs/hwga/status.md, the implemented HWGA06 workflow, and phases/HWGA07_morning_directive_and_recap_chain.md. Inspect repository state and actual data relationships first.

Implement only an idempotent next-day in-app MorningDirective and the V1 recap chain (stored DAILY recaps → WEEKLY recap). MONTHLY/YEARLY remain contract-level only — do not silently implement them. No FCM in V1.

Use deterministic period selection/timezone logic, typed model outputs, evidence grounding, deterministic fallback, and repository/service boundaries. The model must not infer an event that was not recorded. Weekly generation must consume stored daily recap objects (source_recap_ids), not unbounded raw logs. Private media renders only via authenticated references. Avoid guilt, coercion, and comparisons.

Write and run:
  cd backend && uv run pytest tests/test_directive.py tests/test_weekly_recap.py -q -ra
  cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test
Cover timezone/partial windows, missing recap days, idempotency/retries, model failure, and UI empty/fallback states. A check that was not run counts as failed. Comprehensive regression and phone acceptance remain HWGA08.

Finish with the Two-Step Commit Protocol exactly as written in the phase file (implementation commit → hash → status.md docs commit → git push origin main). Report both commit hashes. Stop before HWGA08.
```

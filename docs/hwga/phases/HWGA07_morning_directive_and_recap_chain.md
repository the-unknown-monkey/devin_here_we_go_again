# Phase HWGA07: Morning Directive & Recap Chain

- **Status:** Planned
- **Dependency:** HWGA06 daily recap available
- **Scope:** In-app directive, weekly compaction, and supported recap chronology

## 1. Goal

Use the stored daily receipt and short recent history to produce a concrete next-day action, then demonstrate hierarchical memory by generating a weekly recap from saved Daily recaps rather than replaying every raw event.

## 2. Deliverables

- Deterministic selection of eligible recap/history and active goals for a user's local date.
- Typed Morning Directive workflow: input context -> Gemini proposal -> schema/fact validation -> idempotent persistence.
- Deterministic safe fallback directive if the model/provider fails; no push notification/FCM in V1.
- In-app directive card shown on first relevant app open; mark display/read state without duplicate generation.
- Weekly recap workflow consuming stored daily recap objects, with period completeness/missing-day markers and curated media refs.
- Private chronology view joining recap narratives to authorized media; no public sharing, likes, streak comparison, or social affordance.
- Define contracts for Monthly/Yearly recap lineage; full generation/UI stays post-V1 unless HWGA01 status explicitly approves it.

## 3. Boundaries and Correctness

- Never tell the user to do something based on absent evidence as if it were a fact.
- Keep recommendations small, non-coercive, and connected to a real event or active goal.
- Weekly recap summarizes stored daily recaps; do not send all raw records to the model.
- Ensure timezone, partial weeks, app-open retries, and generation idempotency are deterministic.

## 4. Exit Criteria

- Focused checks cover no recap, missing days, partial week, retry, provider failure, local date change, and duplicate app open.
- Weekly pipeline proves it consumes daily recap records and preserves source/media references.
- In-app directive and chronological recap screens handle empty and fallback states.

## 5. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA07: Morning Directive & Recap Chain.

Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/implementation.md, docs/hwga/status.md, the accepted recap/directive contracts, and the implemented HWGA06 workflow plus this phase. Inspect repository state and actual data relationships first.

Implement only an idempotent next-day in-app Morning Directive and the V1-approved recap chain (daily recap inputs -> weekly recap). Monthly/yearly contracts may be completed only within the accepted scope; do not silently add the full monthly/yearly implementation. No FCM in V1.

Use deterministic period selection/timezone logic, typed model outputs, evidence grounding, deterministic fallback, and repository/service boundaries. The model must not infer an event that was not recorded. Weekly generation must consume stored daily recap objects, not unbounded raw logs. Private media is rendered only via authenticated references. Avoid guilt, coercion, and comparisons.

Run focused checks for timezone/partial windows, missing recap days, idempotency/retries, model failure, and relevant UI empty/fallback states. Keep comprehensive regression and physical-phone acceptance for HWGA08. Record actual commands/results in status; preserve unrelated changes; no commit/push. Stop before HWGA08.
```

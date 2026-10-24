# Post-V1: Nothing Phone UX Refinement & Feature Discovery

- **Status:** Deferred until HWGA08 V1 acceptance
- **Dependency:** HWGA08 passes on Nothing Phone 2a, or user explicitly accepts a documented exception
- **Purpose:** Improve the actual tested product without mixing redesign scope into MVP delivery

## A. Post-V1 UI/UX Refinement

Use the user's Nothing Phone 2a feedback, observed usability friction, accessibility checks, and demo feedback to refine hierarchy, typography, spacing, color, icons, transitions, and motion. Keep the private/no-shame philosophy. Preserve a working baseline and validate each visual change on device. Do not add new product features under the label of polish.

### Copy-Paste Prompt: UX Refinement Conversation

```text
Please begin the Post-V1 UI/UX Refinement phase only after HWGA08 acceptance. Read the complete HWGA docs, status ledger, and HWGA08 evidence first. Inspect actual Flutter screens, device behavior, current tests, and my Nothing Phone 2a feedback before proposing changes.

This phase is visual/interaction refinement, not feature expansion. Identify concrete friction with screen/component references and propose a small prioritized design plan before editing. Preserve accessibility, readable text, purposeful transitions, consistent icons, fast capture, private-by-design behavior, and non-shaming rest/focus language. Avoid a generic dashboard redesign. Ask before changing product semantics or stored data.

Make focused UI changes only after I approve the proposal. Add/run affected widget/analyze checks and verify on the Nothing Phone 2a with my confirmation. Record before/after rationale and exact evidence in status. Preserve unrelated work; no commit/push unless asked.
```

## B. Post-V1 Feature Discovery & Extension

After UX refinement or as separately approved, review user feedback and prioritize additional features. Candidate extensions include Monthly/Yearly recap generation, richer search/filter, export/delete controls, notification options, and additional capture workflows. No candidate is automatically approved.

### Copy-Paste Prompt: Feature Planning Conversation

```text
Please start a separate Post-V1 Feature Discovery conversation. Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/status.md, HWGA08 acceptance evidence, and the post-V1 section. Inspect the current code and feedback; do not assume a candidate feature is desired.

First produce a short evidence-based backlog ranked by user value, implementation risk, privacy/security impact, hackathon/demo relevance, and cost. Include acceptance criteria, service/data boundaries, migration/API impact, test approach, and a phase breakdown for each recommended item. Treat monthly/yearly recaps as candidates, not existing capability. Ask me to choose before implementing anything.

Once a feature is explicitly selected, create a bounded phase specification and update decisions/status before code. Follow the same no-hallucination, service-boundary, privacy, and evidence rules as V1. Do not bundle unrelated features or claim unsupported test results. No commit/push unless requested.
```

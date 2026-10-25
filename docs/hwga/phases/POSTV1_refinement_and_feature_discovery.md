# Post-V1: Nothing Phone UX Refinement & Feature Discovery

- **Phase ID:** POSTV1
- **Branch:** `main`
- **Status:** Deferred until HWGA08 V1 acceptance
- **Dependency:** HWGA08 passes on Nothing Phone 2a, or user explicitly accepts a documented exception
- **Purpose:** Improve the actual tested product without mixing redesign scope into MVP delivery

## A. Post-V1 UI/UX Refinement

Use the user's Nothing Phone 2a feedback, observed usability friction, accessibility checks, and demo feedback to refine hierarchy, typography, spacing, color, icons, transitions, and motion. Keep the private/no-shame philosophy. Preserve a working baseline and validate each visual change on device. Do not add new product features under the label of polish.

### Copy-Paste Prompt: UX Refinement Conversation

```text
Please begin the Post-V1 UI/UX Refinement phase only after HWGA08 acceptance, on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short

Read the complete docs/hwga docs, contracts.md, status.md, and the HWGA08 evidence log first. Inspect actual Flutter screens, device behavior, current tests, and my Nothing Phone 2a feedback before proposing changes.

This phase is visual/interaction refinement, not feature expansion. Identify concrete friction with screen/component references and propose a small prioritized design plan before editing. Preserve accessibility, readable text, purposeful transitions, consistent icons, fast capture, private-by-design behavior, and non-shaming rest/focus language. Avoid a generic dashboard redesign. Ask before changing product semantics or stored data.

Make focused UI changes only after I approve the proposal. Add/run affected widget/analyze checks (dart format --set-exit-if-changed lib test && flutter analyze && flutter test) and verify on the Nothing Phone 2a with my confirmation. Apply the Two-Step Commit Protocol (implementation commit → hash → status.md docs commit → push origin main) for each approved batch. Record before/after rationale and exact evidence in status.md. Preserve unrelated work.
```

## B. Post-V1 Feature Discovery & Extension

After UX refinement or as separately approved, review user feedback and prioritize additional features. Candidate extensions include MONTHLY/YEARLY recap generation (contracts.md already defines their lineage), richer search/filter, export/delete controls, notification options, and additional capture workflows. No candidate is automatically approved.

**User-approved during HWGA08 (2026-10-25), recorded as status.md D26 — implement as bounded post-V1 phase(s):**

1. **Pipeline/results surface:** a dedicated area listing generation status per period — receipt, directive, weekly — including GENERATED vs FALLBACK, timestamps, and linked evidence. Today there is no way to inspect pipeline results in-app.
2. **On-demand generation:** user-triggered receipt/directive generation at any time, computed from data accumulated so far — not only fixed evening/morning schedule points. V1's lazy `GET /recaps` and authenticated `POST /internal/run/{daily|weekly}` are the existing mechanism; the post-V1 work is a user-facing trigger plus clear "data so far" semantics (idempotency and stale rules unchanged).
3. **Android home-screen widgets (status.md D27):** (a) quick-taps widget for one-tap baseline logging without opening the app (idempotent `POST /events`); (b) mode + today widget — mode flip and a single rotating hook line (directive clause / "receipt ready" teaser / goal age) deep-linking into the app. Excludes insights, media, chronology, and narrative text: the widget is a home-screen-visible surface, so counts and chips only per the privacy invariant. Requires native AppWidgetProvider (e.g. `home_widget` package) and native-side access to the Keystore-backed bearer token.

### Copy-Paste Prompt: Feature Planning Conversation

```text
Please start a separate Post-V1 Feature Discovery conversation, on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short

Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/contracts.md, docs/hwga/status.md, the HWGA08 acceptance evidence, and this file. Inspect the current code and feedback; do not assume a candidate feature is desired.

First produce a short evidence-based backlog ranked by user value, implementation risk, privacy/security impact, hackathon/demo relevance, and cost. Include acceptance criteria, service/data boundaries, migration/API impact, test approach, and a phase breakdown for each recommended item. Treat monthly/yearly recaps as candidates, not existing capability. Ask me to choose before implementing anything.

Once a feature is explicitly selected, create a bounded phase specification (same format as the HWGAxx phases: header metadata, exact files/tests/commit protocol, copy-paste prompt) and update decisions/status before code. Follow the same no-hallucination, service-boundary, privacy, and evidence rules as V1. Do not bundle unrelated features or claim unsupported test results.
```

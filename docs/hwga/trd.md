# HWGA Technical Requirements Document

- **Document ID:** TRD-HWGA
- **Project:** Here We Go Again (HWGA)
- **Track:** Make the Invisible Visible
- **Phase Prefix:** `HWGA`
- **Status:** V1 development baseline; phase work not started
- **Repository:** `https://github.com/the-unknown-monkey/devin_here_we_go_again.git`
- **Current branch at documentation baseline:** `main`
- **Companions:** [Product blueprint](../../here_we_go_again.md), [implementation map](implementation.md), [status ledger](status.md), [phase prompts](phases/)

---

## 1. Product and V1 Outcome

HWGA is a private, single-player self-awareness app for people whose days blur together. It captures ordinary physical-care signals, mode changes, sensory moments, and ideas, then turns those records into a grounded nightly receipt and an actionable morning directive. There are no followers, likes, public profiles, or competitive leaderboards.

The target age group is people approximately **20-35 years old**. This describes the intended audience's age range, not the number of users. It is a product focus, not an eligibility restriction. V1 should prove two outcomes:

1. **Sensory proof of a lived day:** the user can revisit real moments and recognize rest as meaningful time.
2. **Useful behavior change:** gentle, evidence-based prompts help the user notice hydration, movement, focus/rest balance, and a goal they may be avoiding.

### V1 must-have loop

1. Capture low-friction confirmations, mode changes, goals, and sensory moments.
2. Persist events and private media through the backend.
3. Aggregate that day's facts deterministically.
4. Produce a structured, grounded daily receipt with Gemini, a deterministic fallback, and a fact-validation gate.
5. Surface the next Morning Directive in-app.
6. Exercise the end-to-end experience on the **Nothing Phone 2a** before UI redesign or feature expansion.

The data model and architecture must support Daily, Weekly, Monthly, and Yearly recaps. V1 prioritizes a complete Daily loop and Weekly roll-up; Monthly/Yearly generation is deferred until V1 acceptance unless the user explicitly expands scope in HWGA01.

## 2. Approved Product and Platform Constraints

- Android app: Flutter/Dart; target acceptance device: Nothing Phone 2a.
- API and domain logic: FastAPI/Python. Pin the project interpreter to Python 3.13 after setup verification.
- Agent orchestration: LangChain/LangGraph in the backend; Gemini is called server-side only.
- Local hackathon persistence: Postgres in Docker; media stored on local disk behind authenticated backend routes.
- Morning Directive delivery: in-app for V1. Firebase Cloud Messaging is deferred.
- Demo access: ngrok on Windows 11 may expose the authenticated FastAPI HTTP port only. Never tunnel Postgres, the Docker daemon, or an unauthenticated debug interface.
- Single-user product/auth scope: no public registration or social graph. HWGA01 must select the concrete local authentication mechanism and record its threat assumptions.
- UI baseline: clean, minimal, modern, coherent; intentional icons and transitions/animations. Defer major visual redesign until full V1 acceptance on the phone.
- Source roots: `flutter/` and `backend/`. At the documentation baseline, both names are zero-byte files, not directories. HWGA02 may replace them with directories as explicitly authorized by the user.

## 3. Functional Requirements

### 3.1 Human baselines and modes

Capture user-confirmed water, food, stretching, posture resets, walking, and quiet moments. Log transitions between `LOCKED_IN` and `PURE_FUN_RECOVERY` with timestamps. Derive durations from valid transitions; do not let the LLM invent or calculate durations.

### 3.2 Rule of 3

- At most three active goals per user, enforced transactionally by the backend.
- Each item has a stable id, creation time, title, and `ACTIVE`, `COMPLETED`, or `RETIRED` state.
- Compute visible age from timestamps and the user's configured timezone; never store a mutable "age in days" counter.
- Adding a fourth active item must fail with a clear, typed response until an active item is completed or retired.

### 3.3 Sensory Moment Vault

- Capture raw photos, 5-10 second ambient audio, and voice scraps.
- Store media outside Postgres; persist metadata, ownership, timestamps, MIME/size/duration, and a backend-controlled storage key in Postgres.
- Require authorization for upload, playback, download, and deletion. Never expose local storage paths or directory listings.
- Provide an explicit text/transcript fallback if transcription is unavailable.

### 3.4 Recaps and directive

- Daily receipt is generated from the selected user's event window and includes narrative, structured insights, media references, and evidence ids.
- Morning Directive is derived from saved recap(s) and current goal state; show it in-app on the next app open.
- Weekly recap consumes stored Daily recaps, not the full raw event history.
- Monthly/yearly recap contracts are designed for future compaction tiers; implementation is post-V1 by default.
- All generation is idempotent by user and local period so retries cannot create duplicate receipts/directives.

## 4. Service Boundaries and Data Flow

```text
Nothing Phone 2a / Flutter
  -> authenticated HTTPS/HTTP API requests only
FastAPI backend
  -> auth, validation, domain rules, orchestration, file access, scheduling
  -> Postgres repository layer (events, goals, media metadata, recaps)
  -> private local media storage adapter (photo/audio/voice bytes)
  -> LangGraph orchestration and Gemini provider adapter
Gemini
  <- minimum structured, user-authorized context required for narrative generation
```

### Ownership rules

- **Flutter** owns presentation, device permissions, capture UX, local transient state, and API calls. It never connects directly to Postgres, the filesystem storage root, or Gemini.
- **FastAPI routers** own HTTP parsing/authentication/response contracts; routers delegate domain work and must not become the home for business calculations.
- **Domain/services** own Rule-of-3 enforcement, mode interval validation, event aggregation, recap eligibility, and deterministic calculations.
- **Repositories** own database access. Agent nodes do not issue ad hoc database queries or bypass repositories.
- **Media storage adapter** owns safe file naming, path confinement, limits, MIME validation, and stream reads/deletes; API clients never receive raw local paths.
- **LangGraph** owns orchestration and typed handoffs. It calls application services/tools, not Flutter, raw SQL, or direct filesystem paths.
- **Gemini adapter** is server-side, replaceable, timeout-bounded, schema-constrained, and isolated from the API contract.
- **Postgres** is private to backend containers/processes. Flutter and ngrok never connect to or expose it.
- **ngrok** is a transport/demo tunnel only, not authentication. Auth remains mandatory with the tunnel active.

## 5. Deterministic Code vs. Gemini

### Deterministic application logic

- Timezone conversion and daily/weekly period boundaries.
- Event validation, mode intervals, durations, baseline counts, and missing-data treatment.
- Rule-of-3 limits and goal aging.
- Structured recap inputs and media-selection eligibility.
- Recap/directive idempotency and persistence.
- Output schema validation, evidence-id checks, and numeric/name fact checks against source context.

### Gemini may

- Summarize validated facts into a compassionate, concise narrative.
- Identify candidate patterns only when supported by provided evidence.
- Suggest one or more concrete actions grounded in actual events and active goals.

### Gemini must not

- Invent events, timestamps, quantities, mood states, diagnoses, streaks, or user intentions.
- Shame the user, treat rest as failure, or infer a clinical/medical condition.
- Override deterministic facts, user mode, or goal state.
- Write directly to Postgres or access media by arbitrary path.

Require structured output (Pydantic/JSON schema), explicit evidence references where practical, bounded retries/timeouts, and a deterministic fallback narrative. Reject or sanitize invalid outputs and record a safe generation status; never swallow errors without an observable result.

## 6. Privacy, Security, and Reliability Invariants

1. HWGA is private by design. No social graph, public share endpoint, analytics ad SDK, or third-party visibility.
2. Gemini keys, auth secrets, and ngrok tokens belong in local environment/secret storage only; never in source, prompts, status docs, screenshots, or commits.
3. Do not send raw media to Gemini by default. Send only transcripts/metadata/selected excerpts needed for the approved feature; any media transmission requires an explicit decision and consent flow.
4. Treat tunnels as public ingress. Require authentication, validate inputs, cap upload size/duration, and never enable permissive debug/CORS settings for a demo.
5. Use separate disposable test data and test DB configuration. Never point automated tests at a user's real dataset or a production target.
6. Keep operations idempotent and safe under retries, duplicate taps, app restarts, and model timeouts.
7. Missing data is unknown, not a negative. Do not infer that an unlogged stretch, meal, or rest period did not happen.
8. Provide clear delete paths for events/goals/media and define local media retention before acceptance.

## 7. UI/UX Constraints

- Target age group: people approximately 20-35 years old (not a user-count target); avoid corporate dashboard language and motivational-guilt patterns.
- V1 visual direction: minimal, clean, modern Android; readable type, deliberate spacing, clear capture actions, consistent icon family, calm but distinguishable mode states.
- Include high-quality purposeful transitions/animations for navigation, capture confirmation, mode changes, and recap reveal. Avoid animation that delays or blocks a quick action.
- Handle permission denial, empty state, loading, upload failure, offline/retry, and long text/audio states.
- Respect accessibility: contrast, touch targets, semantic labels, text scaling, and reduced-motion preference where supported.
- V1 is usability-first, not a full design system exercise. Detailed polish and feature expansion start only after Nothing Phone 2a acceptance.

## 8. Coding-Agent Rules (Mandatory at Every Phase)

1. **Read before editing:** inspect this TRD, implementation map, status, the active phase prompt, relevant source, and current `git status`/branch. Never trust a stale summary over current files.
2. **No invented APIs or files:** search the repository, inspect dependencies, and verify actual names, versions, schemas, paths, and commands before relying on them. Mark unknowns and ask rather than fabricate.
3. **Honor boundaries:** change the owning service only; no Flutter-to-DB/LLM access, agent direct SQL, or media-path leakage.
4. **Keep scope bounded:** implement only the active phase deliverables. Do not pre-implement later phases or opportunistically refactor unrelated code.
5. **Protect the worktree:** preserve user changes; do not reset, clean, checkout over, delete, or overwrite unrelated files. `backend`/`flutter` placeholder replacement is authorized only as the explicit HWGA02 setup task.
6. **No unapproved side effects:** ask before network downloads, elevated permissions, external API calls, deployment, sending data to a third party, or destructive operations. Never expose credentials in chat or logs.
7. **No silent weakening:** no fake production data, swallowed exceptions, skipped tests without reason, test monkeypatches standing in for live behavior, broad `except` returning success, or relaxed validation merely to pass.
8. **Verify truthfully:** run the narrow phase-local compile/lint/contract checks as applicable; report exact commands, results, failures, skips, and limitations. Never claim a check passed unless its output proves it.
9. **Testing schedule:** full automated regression, end-to-end workflow, and physical-phone acceptance are consolidated in the final V1 phase HWGA08, as requested. Small phase-local checks are still required to avoid accumulating broken code; do not claim the complete product is tested before HWGA08.
10. **Status evidence:** update `status.md` with actual decision changes and evidence only. Do not reuse reference-project pass counts, dates, credentials, or deployment state.
11. **Commit discipline:** do not commit or push unless the user requests it. If requested, inspect staged diff, commit only the intended files, report the exact hash; never amend or force-push without explicit request.
12. **Evidence/commit synchronization:** if the user requests commits, commit phase code/tests first and capture its hash; then record that hash and actual verification in `status.md` in a separate docs commit. Push only if explicitly requested. Never invent a commit or test hash.
13. **Phase handoff:** finish with scope completed, changed files, exact verification evidence, unresolved issues, and progress `completed N/9 V1 phases`; stop at the phase boundary.
14. **Human-controlled machine setup:** Phase HWGA00 must inspect first. Ask before installing/downloading software, changing machine-wide PATH/environment, accepting licenses, using admin rights, or configuring a real token.

## 9. Verification Policy

Each phase defines a small exit gate that fits its changes (format/static checks, API contract checks, or manual environment checks). **The complete V1 test campaign occurs in HWGA08**: backend unit/integration tests on disposable DB, Flutter tests/build, API/media/security checks, and a complete physical Nothing Phone 2a scenario through ngrok. A failed gate is fixed and rerun; it is not marked complete with known failures.

## 10. Scope Change Control

V1 is frozen after HWGA01. Any feature added after the freeze must be added to `status.md` with user approval, impact on the demo, privacy/security implications, acceptance criteria, and a decision whether to defer it until post-V1. UI redesign and new feature work belong to the post-V1 phases after HWGA08 passes on the Nothing Phone 2a.

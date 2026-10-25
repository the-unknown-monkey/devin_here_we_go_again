# HWGA V2 Technical Requirements Document

- **Document ID:** TRD-HWGA-V2
- **Status:** Draft baseline — locked after V2A
- **Prerequisite:** V1 ACCEPTED (HWGA08, 2026-10-25) on Nothing Phone 2a. All V1 invariants in [`../trd.md`](../trd.md) remain in force.

## 1. V2 Outcome

Keep the user connected to HWGA without opening the app. Logging friction is the product's biggest attrition risk; the widget surface exists to make capture nearly free and to pull the user back at the right moment — never to replicate the app on the home screen.

V2 must prove two outcomes on the Nothing Phone 2a:

1. **Zero-open capture:** baseline confirmations and mode flips work from the home screen with clear success/failure feedback.
2. **Honest pull-back surface:** one glanceable hook (directive clause / receipt-ready / goal age) deep-links into the app — plus an in-app place to see what the pipeline actually did.

## 2. Approved Scope (from status.md D26/D27)

1. **Quick-taps widget (V2C):** one-tap `POST /events` for WATER / FOOD_CLEAN / STRETCH / POSTURE_RESET / WALK / QUIET_MOMENT with per-tap idempotency keys. No app open required.
2. **Mode + today hook widget (V2D):** current-mode display + flip (`POST /mode`), and one rotating line — directive clause, "receipt ready", or oldest active goal age — that deep-links to the matching in-app screen.
3. **Pipeline/results surface (V2E):** in-app listing of generation status per period (receipt, directive, weekly) with GENERATED/FALLBACK/FAILED, timestamps, stale marker.
4. **On-demand generation (V2E):** user-facing trigger reusing the existing lazy-fetch + `POST /internal/run/{daily|weekly}` mechanism with explicit "data so far" semantics.

Explicitly **out of V2 scope**: media capture/playback in widgets, insights/narrative text on the home screen, weekly chronology in widget form, FCM/notifications, MONTHLY/YEARLY generation.

## 3. Platform and Architecture Constraints (grounded in the real tree)

- **Widget rendering is native Android only.** Flutter does not render home-screen widgets; V2 adds Kotlin `AppWidgetProvider` + `RemoteViews` under `flutter/android/app/src/main/`. Current state (verified): `AndroidManifest.xml` has no `<receiver>` entries; `MainActivity.kt` is an unmodified `FlutterActivity`.
- **Bridge choice is a V2A decision.** Options: `home_widget` package (Dart-side data push + interactivity callbacks) vs fully native (Kotlin reads token + calls API directly). Constraints already verified: token lives in `flutter_secure_storage` under key `hwga_auth_token` (Keystore-backed shared prefs — natively readable on this device, must be re-verified on the target in V2A); `HWGA_API_BASE_URL` is a compile-time dart-define — a pure-native widget needs the base URL passed to the native layer (via `MethodChannel`/`home_widget` data or a `BuildConfig` field — decide in V2A).
- **No widget-specific auth.** The same bearer token gates every call; the widget must never embed, generate, or display the token. A widget with no token shows a "log in first" state and deep-links to the token screen.
- **Server side stays deterministic.** The widget never computes durations, ages, or generation state; it renders what the backend returns. A new lightweight summary endpoint (see contracts_v2 draft) is preferred over the widget stitching `/mode` + `/directive/today` + `/timeline` — fewer calls, one consistent truth, less token traffic.
- **ngrok is still hostile ingress.** Widget API calls go through the same authenticated routes; nothing new is exposed. No unauthenticated widget endpoints.

## 4. Privacy & Security Invariants (V2 additions)

1. The widget is a **home-screen-visible surface**: only counts, chips, mode name, and at most one short hook line. Never render narrative text, media, insight text, journal content, or any identifier another person shoulder-surfing could exploit.
2. Taps are fire-and-forget `POST /events` with `idempotency_key` — retries and double-taps never double-log (V1 contract already guarantees this; the widget must generate a fresh UUID per user tap).
3. Failures surface honestly on the widget (last-tap failed / offline state) — never fake a successful log.
4. Token rotation still works: if `provision-token` is re-run, the widget degrades to the auth-required state instead of failing forever.
5. No new permissions in the manifest beyond widget plumbing (no BOOT_COMPLETED, no location, no background service in V2).

## 5. Update Model

- Widget data refresh triggers: on tap result, on periodic `updatePeriodMillis` (≥30 min — OS floor), and on app resume pushing latest state (via the chosen bridge). No push/FCM in V2.
- Stale UI is acceptable between refreshes; the hook line always carries its computed-at timestamp internally so the app can decide what to show on deep-link.

## 6. Verification Policy

Same policy as V1: phase-local checks required, full campaign in V2F. Widget acceptance requires physical device verification — home-screen round trips cannot be proven in an emulator suite: add widget → tap chips → verify events land in `/timeline` → kill app → verify taps still work → revoke network → verify honest failure → rotate token → verify auth-required state.

## 7. Coding-Agent Rules

All V1 rules (`../trd.md` §8) apply verbatim. V2 additions:

- **Verify widget/platform APIs against installed dependency versions before coding** — `home_widget` (or native equivalents) have versioned APIs; check the resolved version in `pubspec.lock`/Gradle files, never assume names from memory. If `home_widget` (or any new package) is adopted, pin a version published ≥7 days and record the resolved version plus the exact API surface used in `status_v2.md`.
- **Device proof is user-confirmed only.** Any step requiring the Nothing Phone 2a (taps, deep-links, offline, token rotation) is verified by the user executing and reporting; emulator results never count as device proof, and an agent must never self-certify a manual step.
- **Fakes are for unit tests only.** No fake HTTP layer may substitute for a real `POST /events`/`POST /mode` during device verification; injected fakes exist solely to keep Dart bridge logic platform-free in `flutter test`.
- **No dishonest widget state.** No persistent "sending"/optimistic state that survives a failed call, no swallowed broadcast-receiver failures, no cached success painted over an error.
- **No unapproved platform surface.** No new manifest permissions, foreground services, scheduled workers, or additional packages (`workmanager`, background-fetch, etc.) without a decision recorded in `status_v2.md` and user approval.

## 8. Zero-Hallucination Register (V2)

Verified facts about the actual code/environment discovered during V2. Agents must consult this table (plus `implementation_v2.md` §1 anchors) before relying on names, paths, versions, or commands; every phase appends what it verified. Entries must come from real inspection, never assumption.

| Area | Verified fact | Source phase |
|---|---|---|
| Postgres ports | Dev DB `127.0.0.1:55532`, disposable test DB `127.0.0.1:55533` (tmpfs, `db-test` service). Note: V1 `trd.md` §9's older `55432`/`55433` entry was superseded at HWGA02 — compose + runbook are authoritative | Doc audit 2026-10-25 |
| V1 tree anchors | See `implementation_v2.md` §1 — verified against the real tree 2026-10-25 | Doc audit |
| _V2A appends:_ | token-storage readability, `home_widget` resolved version + API surface, base-URL handoff mechanism, refresh cadence | _pending_ |

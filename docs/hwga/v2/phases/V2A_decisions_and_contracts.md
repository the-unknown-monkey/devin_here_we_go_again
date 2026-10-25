# Phase V2A: V2 Decisions, Platform Probes & Contract Lock

- **Phase ID:** V2A | **Branch:** `main` | **Status:** Completed 2026-10-25
- **Dependency:** V1 accepted; `docs/hwga/v2/` baseline exists
- **Scope:** docs + read-only probes only. No feature code.

## 1. Goal

Resolve every open technical question in `implementation_v2.md` §3 with **real probes on the Nothing Phone 2a**, then lock `contracts_v2.md`. Nothing downstream may assume an unprobed answer.

## 2. Probes (run, record output in status_v2.md)

1. **Token readability:** can native Kotlin code read `hwga_auth_token` from the `flutter_secure_storage` shared-prefs on the A142? (Check which storage backend `flutter_secure_storage 11.2.x` uses on Android 15 — EncryptedSharedPreferences vs Keystore-wrapped prefs — by reading its installed source, then verify with a minimal Kotlin probe or the package's own native code.)
2. **Bridge options:** resolve `home_widget` current stable version, its interactivity API surface (background callback on tap without launching the app) and minimum SDK; compare against a fully native `PendingIntent` broadcast + Kotlin-side `HttpURLConnection`/`OkHttp` call.
3. **Base URL handoff:** choose how the native side learns `HWGA_API_BASE_URL` (MethodChannel on app launch, `BuildConfig` field compiled from the same dart-define, or widget data store). Must also work when the app was never opened after install (widget added first) — decide the honest fallback.
4. **Update cadence:** check `updatePeriodMillis` floor and interactive-element support on Android 15 / Nothing OS; decide refresh triggers.

## 3. Decisions to record in `status_v2.md`

Record each as **V2-D02…V2-D05** in `status_v2.md` (rows pre-created; V2-D06 `internal/run` exposure/semantics may also be decided here at contract lock):

- Bridge mechanism (package vs native) + rationale
- Token access path (direct native read vs mirrored via bridge) + fallback when absent — **a failed readability probe must produce an explicitly recorded fallback decision, not an improvised workaround**
- Base-URL handoff + cold-install fallback
- Refresh model (tap-driven / periodic / app-resume push)
- Lock `contracts_v2.md`: WidgetState fields, `/widget/state`, `/pipeline/status`, deep-link table

## 4. Exit Criteria

- Every §2 probe has recorded real output; unknowns are marked unknown, not guessed
- `contracts_v2.md` status → **LOCKED**, user approved
- Two-Step: docs commit → hash → ledger-sync commit → push

## 5. Copy-Paste Prompt

```text
Please execute Phase V2A: V2 Decisions, Platform Probes & Contract Lock on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short

Read docs/hwga/status.md (esp. D26/D27 + HWGA08 evidence), docs/hwga/v2/README.md, trd_v2.md, contracts_v2.md (DRAFT), implementation_v2.md, status_v2.md, and this phase file. This phase is docs + read-only probes — no feature code.

Run the four probes in §2 on the real device/environment and record verbatim output in status_v2.md. Verify library APIs against installed versions (flutter_secure_storage source, resolved home_widget version if evaluated). Do not assume APIs from memory. If any doc contradicts live code or installed dependency APIs, stop, record the discrepancy in status_v2.md, and ask before proceeding.

Record the §3 decisions with my approval, lock contracts_v2.md, then apply the Two-Step Commit Protocol and push origin main. Stop at the phase boundary.
```

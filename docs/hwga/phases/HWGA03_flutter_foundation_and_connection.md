# Phase HWGA03: Flutter Foundation & Nothing Phone Connection

- **Phase ID:** HWGA03
- **Title:** Flutter Foundation & Nothing Phone Connection
- **Branch:** `main`
- **Status:** Planned (0 / 9 completed)
- **Dependency:** HWGA00 + HWGA01 complete; HWGA02 backend ready
- **Next Phase:** HWGA04
- **Scope:** Flutter app shell, API client, configuration, first authenticated device request

## 1. Goal

Create a clean, reliable Flutter Android foundation and prove the Nothing Phone 2a can reach the authenticated FastAPI service. UI is minimal and modern, with purposeful motion/icon conventions, not the post-V1 redesign.

## 2. Required Reading

`docs/hwga/trd.md`, `docs/hwga/contracts.md`, `docs/hwga/implementation.md`, `docs/hwga/status.md`, accepted HWGA01 decisions, and the HWGA02 backend auth/health code.

## 3. Deliverables

- Replace the zero-byte tracked `flutter` file with a Flutter project directory; only after checking Git diff and confirming it is still the authorized placeholder. Commit `pubspec.lock` (D16).
- Organize source per the approved Flutter layout in `implementation.md` (`lib/app/`, `lib/core/`, `lib/features/`).
- Environment-specific API base URL configuration using the D15 route recorded in `status.md`; no secrets, no assumption that phone `localhost` is the Windows host.
- Typed API client (`lib/core/`): auth token/session handling per D07, consistent `ErrorResponse` mapping, timeouts, safe retry policy.
- App shell: navigation, theme/tokens, icon source, loading/empty/error states, readable typography, touch targets, restrained transition pattern.
- Platform permission rationale scaffolding for camera/microphone; request permissions only when the user starts the relevant capture.
- Connect the physical Nothing Phone 2a via the D15-verified route; prove one authenticated request (e.g. `/health` or an auth-protected profile endpoint) succeeds.

## 4. Boundaries

Flutter calls the FastAPI client only. No direct database, filesystem, Gemini, or ngrok-token use in the app. Keep API URL configurable and avoid committing temporary tunnel URLs.

## 5. Exit Criteria

- App builds and installs on Nothing Phone 2a.
- Authenticated health/profile or equivalent safe endpoint succeeds from the phone.
- API failure, expired/invalid auth, and loading states render safely.
- Named checks pass; a check that was not run counts as failed.

## 6. Test Commands

```powershell
cd flutter
dart format --set-exit-if-changed lib test
flutter analyze
flutter test
flutter devices            # confirm Nothing Phone 2a id
flutter run -d <device-id>
```

## 7. Phase Completion & Git Protocol (Two-Step)

1. Run format/analyze/test + device install and the authenticated request; record results.
2. **Step 1 — implementation commit:**
   ```powershell
   git add flutter
   git commit -m "feat(hwga): scaffold Flutter app shell and authenticated phone connection (HWGA03)"
   git rev-parse --short HEAD
   ```
3. **Step 2 — ledger sync + push:** update `status.md` with the real hash and evidence, then:
   ```powershell
   git add docs/hwga/status.md
   git commit -m "docs(hwga): record HWGA03 commit hash in status.md"
   git push origin main
   ```
4. Deliver handoff summary: **Completed 4 / 9; Remaining: 5**.

## 8. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA03: Flutter Foundation & Nothing Phone Connection on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short
  type flutter   # confirm it is still the tracked zero-byte placeholder
  adb devices

Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/contracts.md, docs/hwga/implementation.md, docs/hwga/status.md, the HWGA02 backend auth code, and phases/HWGA03_flutter_foundation_and_connection.md. Inspect the actual Flutter scaffold and installed package versions first; do not assume file paths or package APIs.

I authorized replacing the zero-byte tracked `flutter` file with the Flutter project directory in this phase. Verify it is still the same empty placeholder before replacing it; preserve all unrelated work. Do not change backend foundations outside a needed, documented contract fix.

Implement only the client shell, configurable authenticated API client (using the D15 route + D07 auth recorded in status.md), safe states, minimal visual baseline, and physical-device connection. Commit pubspec.lock. Do not place auth secrets or ngrok/Gemini credentials in the app or repository. Keep all server-owned logic out of Flutter. Add meaningful but restrained transitions/icons, support accessibility/text scaling, defer broad redesign.

Run the phase's named checks:
  cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test
Then install on the Nothing Phone 2a (flutter devices / flutter run -d <id>) and prove one authenticated request to the backend. Capture actual device/API evidence without tokens. If the phone or backend cannot connect, diagnose exact output and stop; do not claim success. A check that was not run counts as failed.

Finish with the Two-Step Commit Protocol exactly as written in the phase file (implementation commit → hash → status.md docs commit → git push origin main). Report both commit hashes. Stop before HWGA04.
```

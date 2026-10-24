# Phase HWGA03: Flutter Foundation & Nothing Phone Connection

- **Status:** Planned
- **Dependency:** HWGA00 and HWGA01 complete; HWGA02 backend ready
- **Scope:** Flutter app shell, API client, configuration, first authenticated device request

## 1. Goal

Create a clean, reliable Flutter Android foundation and prove the Nothing Phone 2a can reach the authenticated FastAPI service. UI is minimal and modern, with purposeful motion/icon conventions, not the post-V1 redesign.

## 2. Deliverables

- Replace the zero-byte tracked `flutter` file with a Flutter project directory; only after checking Git diff and confirming it is still the authorized placeholder.
- Organize source according to the approved Flutter layout in `implementation.md`.
- Add environment-specific API base URL configuration without embedding secrets or local host assumptions.
- Add typed API client, auth token/session handling, consistent error mapping, timeouts, and safe retry policy.
- Add an app shell with navigation, theme/tokens, icon source, loading/empty/error states, readable typography, touch targets, and a restrained transition pattern.
- Add platform permission rationale scaffolding for camera/microphone; request permissions only when the user starts the relevant capture.
- Connect the physical Nothing Phone 2a to the local backend using the HWGA00/HWGA01-verified route. Do not assume phone `localhost` is the Windows host.

## 3. Boundaries

Flutter calls the FastAPI client only. No direct database, filesystem, Gemini, or ngrok-token use in the app. Keep API URL configurable and avoid committing local tunnel URLs if they are temporary.

## 4. Exit Criteria

- App builds and installs on Nothing Phone 2a.
- Authenticated health/profile or equivalent safe endpoint succeeds from the phone.
- API failure, expired/invalid auth, and loading states render safely.
- Phase-local Dart format/analyze/widget checks pass; record exact commands and output.

## 5. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA03: Flutter Foundation & Nothing Phone Connection.

Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/implementation.md, docs/hwga/status.md, accepted HWGA01 contracts, relevant backend API/auth code, and this phase file. Inspect the worktree and actual Flutter scaffold first; do not assume file paths or package APIs.

The user authorized replacing the zero-byte tracked `flutter` file with the Flutter project directory in this phase. Verify it is still the same empty placeholder before replacing it; preserve all unrelated or newly changed work. Do not change backend foundations outside a needed, documented contract fix.

Implement only the client shell, configurable authenticated API client, safe states, minimal visual baseline, and physical-device connection. Use the selected Flutter/Dart versions from HWGA00. Do not place auth secrets or ngrok/Gemini credentials in the app or repository. Keep all server-owned logic out of the Flutter layer. Add meaningful but restrained transitions/icons and support accessibility/text scaling; defer broad redesign.

Run only focused format/analyze/widget/build checks needed for this phase and install/test on the Nothing Phone 2a. Capture actual device/API evidence without tokens. If the phone or backend cannot connect, diagnose exact output and stop; do not claim success. Update status with evidence and limitations. No commit/push. Stop before HWGA04.
```

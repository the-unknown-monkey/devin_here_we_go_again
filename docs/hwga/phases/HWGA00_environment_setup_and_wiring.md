# Phase HWGA00: Windows 11 Setup, Installation & Wiring Verification

- **Phase ID:** HWGA00
- **Title:** Windows 11 Setup, Installation & Wiring Verification
- **Branch:** `main`
- **Status:** Planned (0 / 9 completed)
- **Dependency:** None; first executable implementation phase
- **Next Phase:** HWGA01
- **Scope:** Inspect and prepare the developer machine; no application code
- **Target device:** Nothing Phone 2a

## 1. Goal

Verify that the Windows 11 machine is ready to build, run, and demo the Flutter Android app and FastAPI backend. Audit first, install only what is missing, and prove every tool is wired together before product development starts.

## 2. Required Reading

1. `docs/hwga/trd.md` — especially Coding-Agent Rules, Codebase Reality Anchors, and privacy boundaries.
2. `docs/hwga/implementation.md` — observed environment baseline and readiness commands.
3. `docs/hwga/status.md` — record actual results and blockers.
4. `here_we_go_again.md` — approved stack and source roots.

## 3. Scope & Deliverables

1. Recheck Git status/branch/remote; do not modify or clean user work.
2. Verify Python 3.13, `uv`, Flutter/Dart, Android Studio/SDK/JBR, Docker Desktop engine, and ngrok agent.
3. Verify Flutter sees the Android toolchain with `flutter doctor -v`. **Known issue:** `flutter --version` hung during the doc audit; if any Flutter command stalls, capture the exact stall point, check `C:\src\flutter` and Dart cache integrity, and report rather than retrying blindly.
4. Connect the Nothing Phone 2a: enable Developer Options and USB debugging, authorize this PC, and confirm `adb devices` shows `device`. Install the OEM USB driver only if the device is not detected.
5. Configure Android SDK variables/PATH if required. Before changing user/machine environment, show the exact change and request approval; prefer user-level settings.
6. Install ngrok only if still missing and after explicit approval for download/install. Configure the auth token without printing it. Do not start a public tunnel in this phase.
7. Start/verify Docker Desktop; prove a disposable Postgres container can start, become healthy, accept a local connection/query, and stop cleanly. Do not use personal or production data.
8. Verify project Python interpreter is 3.13; `py` currently defaults to 3.14, so record how the correct interpreter is selected.
9. **Decide the phone↔host dev route** (decision D15): prefer `adb reverse tcp:<port> tcp:<port>` (USB); record the chosen route and exact URL shape in `status.md`. ngrok is the demo path, not the default dev path.
10. Update `implementation.md` and `status.md` with observed versions, exact verified output, setup changes, and remaining blockers. Add verified facts to the TRD Codebase Reality Anchors table. Do not create or replace `backend/` or `flutter/` source paths in this phase.

## 4. Safety and Approval Gates

- Inspect before installing. No downloads, network calls, admin commands, license acceptance, or environment changes without asking first.
- Never put ngrok/Gemini/auth secrets in chat, logs, Markdown, screenshots, shell history, or Git.
- Never expose Postgres through ngrok. Do not tunnel until a later phase has authentication and a working API.
- If a prerequisite cannot be verified safely, mark it blocked and ask the user; do not claim setup complete.

## 5. Exit Criteria

- `flutter doctor -v` has no blocking Android toolchain issue, or each remaining warning has an approved workaround recorded.
- Nothing Phone 2a appears authorized as `device` in `adb devices`.
- Python 3.13 and Docker client + engine are verified; disposable Postgres health/connectivity check succeeds.
- ngrok version is verified and its credential is stored locally without disclosure; no tunnel is active.
- D15 phone↔host route is recorded in `status.md`.
- Status and implementation docs reflect real results, with no invented pass state. A check that was not run counts as failed.

## 6. Phase Completion & Git Protocol (Two-Step)

This is a docs-only phase: single docs commit.

```powershell
git add docs/hwga/status.md docs/hwga/implementation.md docs/hwga/trd.md
git commit -m "docs(hwga): record verified environment baseline (HWGA00)"
git push origin main
```

Deliver handoff summary: **Completed 1 / 9; Remaining: 8**.

## 7. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA00: Windows 11 Setup, Installation & Wiring Verification on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short
  git remote -v

Read in order: docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/implementation.md, docs/hwga/status.md, and phases/HWGA00_environment_setup_and_wiring.md. Inspect tool versions, environment variables, Android SDK, and connected devices before changing anything. Do not assume the prior environment inventory is still accurate. Note: `flutter --version` previously hung — if it stalls, capture the exact stall and diagnose rather than retry blindly.

This phase is setup only: no application code and do not create/replace the backend or flutter source paths. Verify Flutter/Android Studio/SDK/JBR, Python 3.13, uv, Docker Desktop + disposable Postgres, ngrok, and my Nothing Phone 2a USB debugging. Ask before any network download, installation, admin action, license acceptance, machine/user environment change, or use/configuration of a real secret. Show one exact proposed change at a time and wait for approval. Never echo secrets. Never start a public ngrok tunnel or expose Postgres.

Decide and record in status.md (decision D15) the phone-to-host dev route, preferring `adb reverse` over ngrok for development.

Use PowerShell commands and record their actual output. If a check fails, diagnose from its exact output; do not mark the phase complete or continue around a blocker by guessing. Update only the environment/status documentation with verified facts, and add verified entries to the TRD Codebase Reality Anchors table. Preserve all user files and changes.

Finish with the Two-Step Protocol (docs-only single commit): stage docs/hwga files, commit "docs(hwga): record verified environment baseline (HWGA00)", push origin main. Report exact commit hash.

Exit only when the phase exit criteria pass or clearly report blockers. In your final message list changes, versions, exact verification evidence, failures/skips, remaining blockers, commit hash, and confirm no application code changed. Stop before HWGA01.
```

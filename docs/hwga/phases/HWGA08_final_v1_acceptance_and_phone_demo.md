# Phase HWGA08: Final V1 Regression, Nothing Phone 2a Acceptance & Demo

- **Phase ID:** HWGA08
- **Title:** Final V1 Regression, Nothing Phone 2a Acceptance & Demo
- **Branch:** `main`
- **Status:** Planned (0 / 9 completed)
- **Dependency:** HWGA00–HWGA07 complete; no known blocking defect
- **Next Phase:** Post-V1 (deferred)
- **Scope:** Comprehensive test campaign, real-device acceptance, controlled ngrok demo, verified runbook

## 1. Goal

Prove the complete V1 works as a private end-to-end product on the user's Nothing Phone 2a, with backend persistence, media, recap, directive, privacy boundaries, and demo access verified. This is the final V1 test phase; do not begin post-V1 polish/features until it passes or the user explicitly accepts documented limitations.

## 2. Preflight

- Confirm clean/understood Git state on `main`; preserve user edits.
- Reconfirm separate disposable test database and no production/personal target.
- Verify local direct phone connection (D15 route) and API auth before opening ngrok.
- Verify ngrok account config exists without displaying or recording its token.
- Review all previous phase evidence logs in `status.md` §5 and resolve missing evidence before proceeding — a phase without recorded evidence is treated as unverified.

## 3. Full Acceptance Matrix

1. Backend format/type/lint and complete unit/API/integration suites against disposable Postgres.
2. Flutter format/analyze/widget tests and Android build/install.
3. Data rules: Rule of 3 under concurrent requests, event timestamps/timezone boundaries, missing data as unknown, mode intervals, recap/directive idempotency.
4. Media: phone photo/audio/voice round trip, ownership checks, invalid/oversized content rejection, deletion, and no public path access.
5. AI: grounded recap and directive; schema-invalid, unsupported facts, timeout/quota, and deterministic fallback scenarios.
6. Private user journey on Nothing Phone 2a: authenticate → log baseline/mode → create/age/resolve goals → capture media → generate/view nightly receipt → reopen for directive → view weekly chronology.
7. UI behavior: animations/transitions do not block capture or navigation; permissions denied, offline/retry, loading, empty, text scaling, and reduced-motion behavior.
8. ngrok: expose only FastAPI with authentication, verify API from the device/network path, verify unauthenticated requests fail, and verify Postgres is not reachable via tunnel.

## 4. Runbook Gate

Only after tests and live phone/demo checks succeed, and after the user confirms the runbook is wanted, create `docs/hwga/runbook.md` with actual PowerShell commands, timestamps/timezone, environment/version evidence, tunnel lifecycle, safe shutdown, and troubleshooting. Never write fake/sample commands as verified and never include real credentials or public tokens.

## 5. Test Commands

```powershell
cd backend && uv run pytest tests -q -ra
cd ..\flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test && flutter build apk --debug
adb devices
ngrok http <HWGA01-port>   # only after user approval, auth confirmed
```

## 6. Exit Criteria

- Full suites and scenario matrix pass, or each remaining failure is fixed and rerun.
- Nothing Phone 2a manual acceptance is explicitly confirmed by the user; record OS/build/device and observed result without collecting unrelated private media.
- ngrok test verifies authorization and confirms DB is not exposed.
- Status records exact outputs, failures/skips, limitations, and final V1 acceptance decision.
- User explicitly approves runbook creation; otherwise leave it absent.

## 7. Phase Completion & Git Protocol (Two-Step)

1. Run the acceptance matrix; fix and rerun failures.
2. **Step 1 — implementation commit** (fixes + runbook if approved):
   ```powershell
   git add backend flutter docs/hwga/runbook.md
   git commit -m "fix(hwga): resolve V1 acceptance findings and add verified runbook (HWGA08)"
   git rev-parse --short HEAD
   ```
3. **Step 2 — ledger sync + push:** update `status.md` with final evidence + V1 acceptance decision, then:
   ```powershell
   git add docs/hwga/status.md
   git commit -m "docs(hwga): record HWGA08 acceptance evidence and V1 decision"
   git push origin main
   ```
4. Deliver handoff summary: **Completed 9 / 9 V1 phases**.

## 8. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA08: Final V1 Regression, Nothing Phone 2a Acceptance & Demo on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short
  adb devices

Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/contracts.md, docs/hwga/implementation.md, docs/hwga/status.md (including every completed phase's evidence log in §5), and phases/HWGA08_final_v1_acceptance_and_phone_demo.md. Do not rely on old pass counts or assume any phase is complete without status evidence — treat a phase with no recorded evidence as unverified.

This is the final comprehensive V1 validation phase. First verify test isolation (disposable local data only, never production/personal). Run the repository's actual commands for backend, Flutter, API/media/security, Android build, and end-to-end scenarios; do not invent commands or suppress failures. Fix defects within agreed scope, rerun affected checks, and record actual output.

Coordinate the Nothing Phone 2a scenario with me: ask me to execute any required manual actions and report what I observe. Do not claim device acceptance without my confirmation. Ask before starting ngrok or making the backend reachable from outside the machine. If approved, provide/run one safe step at a time, expose only the authenticated API, never expose Postgres, and verify unauthorized requests fail. Never reveal ngrok/Gemini/auth tokens.

Do not begin UI redesign or feature expansion in this phase. Create docs/hwga/runbook.md only after the acceptance checks pass and I explicitly confirm; include only commands actually verified and no secrets.

Finish with the Two-Step Commit Protocol exactly as written in the phase file (implementation commit → hash → status.md docs commit recording the V1 acceptance decision → git push origin main). Report both commit hashes, remaining limitations, and the V1 acceptance decision. Stop before post-V1 work.
```

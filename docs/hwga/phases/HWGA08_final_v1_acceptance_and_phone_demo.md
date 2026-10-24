# Phase HWGA08: Final V1 Regression, Nothing Phone 2a Acceptance & Demo

- **Status:** Planned
- **Dependency:** HWGA00-HWGA07 complete; no known blocking defect
- **Scope:** Comprehensive test campaign, real-device acceptance, controlled ngrok demo, verified runbook

## 1. Goal

Prove the complete V1 works as a private end-to-end product on the user's Nothing Phone 2a, with backend persistence, media, recap, directive, privacy boundaries, and demo access verified. This is the final V1 test phase; do not begin post-V1 polish/features until it passes or the user explicitly accepts documented limitations.

## 2. Preflight

- Confirm clean/understood Git state and current branch; preserve user edits.
- Reconfirm separate disposable test database and no production/personal target.
- Verify local direct phone connection and API auth before opening ngrok.
- Verify ngrok account config exists without displaying or recording its token.
- Review all previous phase exit records and resolve missing evidence.

## 3. Full Acceptance Matrix

1. Backend format/type/lint and complete unit/API/integration suites against disposable Postgres.
2. Flutter format/analyze/widget tests and Android build/install.
3. Data rules: Rule of 3 under concurrent requests, event timestamps/timezone boundaries, missing data as unknown, mode intervals, recap/directive idempotency.
4. Media: phone photo/audio/voice round trip, ownership checks, invalid/oversized content rejection, deletion, and no public path access.
5. AI: grounded recap and directive; schema-invalid, unsupported facts, timeout/quota, and deterministic fallback scenarios.
6. Private user journey on Nothing Phone 2a: authenticate -> log baseline/mode -> create/age/resolve goals -> capture media -> generate/view nightly receipt -> reopen for directive -> view weekly chronology.
7. UI behavior: animations/transitions do not block capture or navigation; permissions denied, offline/retry, loading, empty, text scaling, and reduced-motion behavior.
8. ngrok: expose only FastAPI with authentication, verify API from the device/network path, verify unauthenticated requests fail, and verify Postgres is not reachable via tunnel.

## 4. Runbook Gate

Only after tests and live phone/demo checks succeed, and after the user confirms the runbook is wanted, create `docs/hwga/runbook.md` with actual PowerShell commands, timestamps/timezone, environment/version evidence, tunnel lifecycle, safe shutdown, and troubleshooting. Never write fake/sample commands as verified and never include real credentials or public tokens.

## 5. Exit Criteria

- Full suites and scenario matrix pass, or each remaining failure is fixed and rerun.
- Nothing Phone 2a manual acceptance is explicitly confirmed by the user; record OS/build/device and observed result without collecting unrelated private media.
- ngrok test verifies authorization and confirms DB is not exposed.
- Status records exact outputs, failures/skips, limitations, and final V1 acceptance decision.
- User explicitly approves runbook creation; otherwise leave it absent.

## 6. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA08: Final V1 Regression, Nothing Phone 2a Acceptance & Demo.

Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/implementation.md, docs/hwga/status.md, every completed phase's evidence, and this acceptance matrix. Inspect Git status/branch and test configuration. Do not rely on old pass counts or assume any phase is complete without status evidence.

This is the final comprehensive V1 validation phase. First verify test isolation and confirm tests use only disposable local data. Run the exact current repository commands for backend, Flutter, API/media/security, Android build, and end-to-end scenarios; do not invent commands or suppress failures. Fix defects within agreed scope, rerun affected checks, and record actual output. Never test against production/personal data.

Coordinate the Nothing Phone 2a scenario with me: ask me to execute any required manual actions and report what I observe. Do not claim device acceptance without my confirmation. Ask before starting ngrok or making the backend reachable from outside the machine. If approved, provide/run one safe step at a time, expose only the authenticated API, never expose Postgres, and verify unauthorized requests fail. Never reveal ngrok/Gemini/auth tokens.

Do not begin UI redesign or feature expansion in this phase. Create docs/hwga/runbook.md only after the acceptance checks pass and I explicitly confirm; include only commands actually verified and no secrets. Update status with exact test/device/network evidence, remaining limitations, and the V1 acceptance decision. No commit/push unless I ask. Stop before post-V1 work.
```

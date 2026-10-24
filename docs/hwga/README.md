# HWGA Development Documentation

This documentation set is the source of truth for the **Here We Go Again (HWGA)** hackathon MVP. Read the product blueprint first, then the technical requirements and implementation map before executing a phase.

## Authority and Reading Order

1. [`../../here_we_go_again.md`](../../here_we_go_again.md) — product vision, V1 features, pipeline overview, and agreed hackathon scope.
2. [`trd.md`](trd.md) — technical decisions, service boundaries, privacy/security invariants, and coding-agent rules.
3. [`implementation.md`](implementation.md) — planned repository layout, local environment, setup verification, and test strategy.
4. [`status.md`](status.md) — current decisions, phase status, observed environment, and evidence. This file records actual state only.
5. [`phases/`](phases/) — self-contained phase specifications with copy-ready prompts for new coding-agent conversations.
6. `runbook.md` — intentionally not created until HWGA08 demo commands have been executed and verified.

## Document Governance

- The product blueprint says **what and why**; the TRD says **what must remain true**; implementation and phase docs say **where and how**.
- If source code, environment state, or a live command contradicts a document, stop, inspect the evidence, and record the discrepancy in `status.md`. Do not guess which is correct.
- A coding agent may make a focused, user-approved decision only after recording it in `status.md`; otherwise ask before dependent work.
- Update status with observed facts and real command/test output. Never copy old pass counts, machine secrets, tokens, or deployment output.
- Update the relevant authoritative document when an approved decision changes. Do not silently leave contradictory instructions in place.

## Phase Index

| Phase | Objective | Status |
|---|---|---|
| [HWGA00](phases/HWGA00_environment_setup_and_wiring.md) | Check, install with approval, and verify the Windows/Android development environment | Planned |
| [HWGA01](phases/HWGA01_decisions_and_contracts.md) | Freeze V1 decisions and typed contracts | Planned |
| [HWGA02](phases/HWGA02_backend_foundation.md) | Establish FastAPI, Postgres, migrations, auth, and isolated test infrastructure | Planned |
| [HWGA03](phases/HWGA03_flutter_foundation_and_connection.md) | Establish Flutter app structure and authenticated phone-to-API connection | Planned |
| [HWGA04](phases/HWGA04_daily_baselines_and_rule_of_three.md) | Implement daily check-ins, modes, timeline, and Rule of 3 | Planned |
| [HWGA05](phases/HWGA05_sensory_moment_vault.md) | Implement photo/audio/voice capture and private media handling | Planned |
| [HWGA06](phases/HWGA06_nightly_receipt.md) | Implement daily aggregation, Gemini receipt, fallback, and fact guard | Planned |
| [HWGA07](phases/HWGA07_morning_directive_and_recap_chain.md) | Implement in-app directive and recap chain in the agreed V1 scope | Planned |
| [HWGA08](phases/HWGA08_final_v1_acceptance_and_phone_demo.md) | Run full regression, Nothing Phone 2a acceptance, and ngrok demo gate | Planned |
| [Post-V1](phases/POSTV1_refinement_and_feature_discovery.md) | Refine UI/UX and select further features after V1 phone acceptance | Deferred |

## Reference Method

The phase organization follows the user's tested pipeline-doc method: initial read-only audit, explicit decision/contracts foundation, implementation map, one bounded phase per conversation, evidence-based status, an integrated acceptance gate, and a verified runbook only after the final rollout/demo gate. The business-agent monorepo's service names, Shopify assumptions, cloud resources, and credentials are not HWGA requirements.

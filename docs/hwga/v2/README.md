# HWGA V2 Development Documentation

V2 scope: **Android home-screen widgets** plus the two related user-approved items from HWGA08 (status.md D26/D27): an in-app pipeline/results surface and on-demand generation.

This documentation set follows the same method as V1: blueprint → TRD → contracts → implementation map → status ledger → bounded phase specs. Read the V1 docs first for context — V1 contracts and invariants remain authoritative unless a V2 doc explicitly amends them with an approved decision.

## Authority and Reading Order

1. [`../README.md`](../README.md) + [`../status.md`](../status.md) — V1 decisions (D01–D27), acceptance evidence. D26/D27 are the approved V2 scope seeds.
2. [`../contracts.md`](../contracts.md) — V1 locked enums/models/API. V2 adds surface; it must not reshape V1 contracts.
3. [`trd_v2.md`](trd_v2.md) — V2 technical decisions, widget platform boundaries, privacy rules.
4. [`contracts_v2.md`](contracts_v2.md) — V2 additions only (widget state surface, widget-safe error cases). **DRAFT until V2A locks it.**
5. [`implementation_v2.md`](implementation_v2.md) — file map **written against the real V1 tree**; phase↔file matrix; test strategy.
6. [`status_v2.md`](status_v2.md) — V2 decision register, phase status, evidence log.
7. [`phases/`](phases/) — self-contained phase specs with copy-ready prompts.

## Phase Index

| Phase | Objective | Status |
|---|---|---|
| [V2A](phases/V2A_decisions_and_contracts.md) | Lock V2 decisions and widget contracts | Completed |
| [V2B](phases/V2B_backend_widget_surface.md) | Lightweight widget state endpoint + on-demand trigger surface | Planned |
| [V2C](phases/V2C_quick_taps_widget.md) | Quick-taps widget: one-tap baseline logging without opening the app | Planned |
| [V2D](phases/V2D_mode_today_widget.md) | Mode + today hook widget: mode flip + rotating hook line deep-linking into the app | Planned |
| [V2E](phases/V2E_pipeline_surface_and_on_demand.md) | In-app pipeline/results surface + user-facing on-demand generation | Planned |
| [V2F](phases/V2F_v2_acceptance.md) | Full V2 regression, widget acceptance on Nothing Phone 2a, runbook update | Planned |

## Document Governance

Same rules as V1 (`../README.md` §Document Governance) apply verbatim: evidence over documents, record decisions before dependent work, never copy pass counts or secrets, and update `status_v2.md` with real command output only.

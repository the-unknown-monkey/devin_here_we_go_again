# Phase HWGA02: FastAPI, Database & Backend Foundation

- **Status:** Planned
- **Dependency:** HWGA01 contracts accepted
- **Scope:** Backend skeleton, local persistence, auth baseline, health/configuration

## 1. Goal

Create the smallest maintainable FastAPI foundation in `backend/` that can safely persist one user's data, keep media private, and support isolated tests. Replace the zero-byte `backend` file with the intended source directory only as this phase's explicit first repository change.

## 2. Required Reading

`here_we_go_again.md`, `docs/hwga/trd.md`, `docs/hwga/implementation.md`, `docs/hwga/status.md`, and the accepted HWGA01 contracts.

## 3. Deliverables

- Backend Python project metadata/lock and repeatable Python 3.13 environment.
- FastAPI app factory/entry point, settings validation, structured safe logging, and health route.
- Postgres Docker Compose for local development; migrations and repository/session layer.
- Separate disposable test DB configuration; guard against tests using the local app DB.
- The selected single-user auth mechanism, secret bootstrap, and protected API dependency.
- Typed foundational models and repositories for users/configuration, events, mode intervals, goals, media metadata, recaps, and directives as approved in HWGA01.
- Local media storage adapter scaffold with path confinement, safe generated names, and limits; no public static directory mount.
- Safe `.env.example`, `.gitignore`, and setup instructions; no real `.env` or secret value committed.

## 4. Boundaries

Routers validate/authorize then call application services. Services implement rules and use repositories. Agent orchestration is added later and may call services only. No client-facing router performs inline SQL or raw file operations. No direct Gemini call in this phase.

## 5. Exit Criteria

Local backend starts with documented config; health route is responsive; migration applies to disposable/local test DB safely; auth rejects missing/invalid credentials; logs redact secrets; targeted foundation checks pass. Report any intentionally deferred schema/API details rather than inventing them.

## 6. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA02: FastAPI, Database & Backend Foundation.

Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/implementation.md, docs/hwga/status.md, the accepted HWGA01 contracts, and this phase. Inspect current git status/branch, existing files, environment, and installed dependency versions before editing. Treat source code as truth; do not assume a scaffold exists.

Implement only the backend foundation deliverables. The user explicitly authorized replacing the zero-byte tracked `backend` file with a directory in this phase; inspect it and the staged/unstaged diff first, then make only that scoped replacement. Do not change the `flutter` placeholder. Preserve unrelated work.

Use Python 3.13 and the dependency/migration/auth choices recorded in HWGA01; if absent or contradictory, stop and ask rather than choose. Keep FastAPI routers, application/domain services, repositories, media storage, and future agent code within the documented ownership boundaries. Never add secrets to source or logs, expose local media as static files, or point tests at personal/production data. Do not add Gemini functionality yet.

Add only focused foundation tests/checks and run the documented narrow commands. Report exact command output, results, failures/skips, files changed, and any migration or security caveats. Update status.md only with observed evidence. Do not commit/push, do not start the next phase, and do not claim full V1 acceptance.
```

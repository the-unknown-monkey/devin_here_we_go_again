# Phase HWGA02: FastAPI, Database & Backend Foundation

- **Phase ID:** HWGA02
- **Title:** FastAPI, Database & Backend Foundation
- **Branch:** `main`
- **Status:** Planned (0 / 9 completed)
- **Dependency:** HWGA01 contracts accepted
- **Next Phase:** HWGA03
- **Scope:** Backend skeleton, local persistence, auth baseline, health/configuration

## 1. Goal

Create the smallest maintainable FastAPI foundation in `backend/` that can safely persist one user's data, keep media private, and support isolated tests. Replace the zero-byte `backend` file with the intended source directory only as this phase's explicit first repository change.

## 2. Required Reading

`here_we_go_again.md`, `docs/hwga/trd.md`, `docs/hwga/contracts.md` (authoritative shapes), `docs/hwga/implementation.md`, `docs/hwga/status.md`, and the accepted HWGA01 decisions.

## 3. Deliverables

- `backend/pyproject.toml` + `uv.lock` on Python 3.13 (D08, D16); `.env.example`, `.gitignore`.
- `backend/app/main.py` FastAPI app factory/entry point, `app/core/` settings validation + structured safe logging, `/health` route.
- `backend/docker-compose.yml` Postgres for local dev (no public DB port); `backend/migrations/` + `app/db/` session/repository layer per the HWGA01 ORM decision.
- Separate disposable test DB configuration (port recorded in status.md); guard against tests using the local app DB.
- The selected single-user auth mechanism (D07), secret bootstrap, and protected API dependency.
- Typed models/repositories matching `contracts.md` §2: users/configuration, events, mode intervals, goals, media metadata, recaps, directives.
- `app/storage/` local media storage adapter scaffold: path confinement, generated names, limits; no public static mount.
- `backend/tests/` foundation tests (health, auth rejection, migration applies on disposable DB, secret redaction).

## 4. Boundaries

Routers validate/authorize then call application services. Services implement rules and use repositories. Agent orchestration is added later and may call services only. No client-facing router performs inline SQL or raw file operations. No direct Gemini call in this phase.

## 5. Exit Criteria

Local backend starts with documented config; `/health` responds; migration applies to disposable test DB; auth rejects missing/invalid credentials; logs redact secrets; the named foundation tests pass. Report any intentionally deferred schema/API details rather than inventing them.

## 6. Test Commands

```powershell
cd backend
uv sync
uv run pytest tests -q -ra
uv run uvicorn app.main:app --port <HWGA01-port>   # then curl http://127.0.0.1:<port>/health
```

## 7. Phase Completion & Git Protocol (Two-Step)

1. Run the tests above; confirm pass counts.
2. **Step 1 — implementation commit:**
   ```powershell
   git rm backend   # remove tracked zero-byte placeholder first (git add -A also works)
   git add backend
   git commit -m "feat(hwga): scaffold FastAPI backend, Postgres, auth, isolated tests (HWGA02)"
   git rev-parse --short HEAD
   ```
3. **Step 2 — ledger sync + push:** update `status.md` (phase table + §5 evidence log) with the real hash and test counts, then:
   ```powershell
   git add docs/hwga/status.md
   git commit -m "docs(hwga): record HWGA02 commit hash in status.md"
   git push origin main
   ```
4. Deliver handoff summary: **Completed 3 / 9; Remaining: 6**.

## 8. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA02: FastAPI, Database & Backend Foundation on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short
  type backend   # confirm it is still the tracked zero-byte placeholder

Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/contracts.md, docs/hwga/implementation.md, docs/hwga/status.md, and phases/HWGA02_backend_foundation.md. Inspect installed dependency versions before editing. Treat source code as truth; do not assume a scaffold exists.

Implement only the backend foundation deliverables in the phase file. I explicitly authorized replacing the zero-byte tracked `backend` file with a directory in this phase; inspect it and the staged/unstaged diff first, then make only that scoped replacement. Do not change the `flutter` placeholder. Preserve unrelated work.

Use Python 3.13 and the dependency/migration/auth choices locked in HWGA01 (contracts.md + status.md decisions); if absent or contradictory, stop and ask rather than choose. Keep FastAPI routers, application/domain services, repositories, media storage, and future agent code within the documented ownership boundaries. Never add secrets to source or logs, expose local media as static files, or point tests at personal/production data. No Gemini functionality yet.

Add only focused foundation tests and run:
  cd backend && uv sync && uv run pytest tests -q -ra
Then verify /health via uvicorn on the HWGA01 port. Report exact command output, results, failures/skips, files changed, and any migration or security caveats. A check that was not run counts as failed.

Finish with the Two-Step Commit Protocol exactly as written in the phase file (implementation commit → hash → status.md docs commit → git push origin main). Report both commit hashes. Stop before HWGA03.
```

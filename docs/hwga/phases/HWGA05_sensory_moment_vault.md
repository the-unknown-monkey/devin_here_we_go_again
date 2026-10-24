# Phase HWGA05: Sensory Moment Vault

- **Phase ID:** HWGA05
- **Title:** Sensory Moment Vault
- **Branch:** `main`
- **Status:** Planned (0 / 9 completed)
- **Dependency:** HWGA02 storage/auth foundation + HWGA03 phone connection; HWGA04 preferred
- **Next Phase:** HWGA06
- **Scope:** Raw photos, ambient audio, voice scraps, private media lifecycle

## 1. Goal

Let the user preserve sensory moments without turning capture into a public or performative post. Implement a private, authenticated media round trip with safe local storage.

## 2. Required Reading

`docs/hwga/trd.md` (service boundaries/privacy), `docs/hwga/contracts.md` (MediaAssetMeta, MediaKind, TranscriptState, `/media` routes), `docs/hwga/implementation.md`, `docs/hwga/status.md`, and the HWGA01 media/transcription decisions.

## 3. Deliverables

- Flutter raw photo capture/pick flow (`lib/features/vault/`) with camera permission at point of use.
- Ambient sound recording capped at the HWGA01-approved 5–10 s; show recording state and duration.
- Voice scrap recording with `MANUAL_TEXT` fallback; honor the HWGA01 transcription provider decision.
- Backend `POST /media` upload + `GET`/`DELETE /media/{id}` playback/download/delete (contracts.md §3).
- Metadata persistence per `MediaAssetMeta`: owner, kind, captured_at, MIME, byte_length, duration_sec, transcript_state, opaque storage key (never returned).
- Storage adapter: generated filenames, path confinement, accepted MIME, size/duration limits, ownership checks, safe delete. Local media dir in `.gitignore`.
- Timeline cards for `IMAGE`/`AUDIO`/`VOICE` with playback and understandable permission/network/storage errors.
- Tests: `backend/tests/test_media.py` covering unauthorized access, invalid MIME, oversize, over-duration, ownership, delete; capture widget tests.

## 4. Privacy Boundaries

- Never mount local media as a public static directory.
- Never trust client filenames, MIME values, filesystem paths, or ownership ids.
- Do not send raw media to Gemini in this phase. Transcription follows HWGA01 and must not expose credentials.
- Do not log transcripts or private media URLs.

## 5. Exit Criteria

- A phone-created sample uploads, is fetched by its owner, plays/views, and deletes.
- An unauthenticated/foreign request cannot access that media.
- Named tests pass; a check that was not run counts as failed.

## 6. Test Commands

```powershell
cd backend && uv run pytest tests/test_media.py -q -ra
cd ..\flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test
```

## 7. Phase Completion & Git Protocol (Two-Step)

1. Run the commands above + one phone round-trip; record results.
2. **Step 1 — implementation commit:**
   ```powershell
   git add backend flutter
   git commit -m "feat(hwga): implement private Sensory Moment Vault media lifecycle (HWGA05)"
   git rev-parse --short HEAD
   ```
3. **Step 2 — ledger sync + push:** update `status.md`, then:
   ```powershell
   git add docs/hwga/status.md
   git commit -m "docs(hwga): record HWGA05 commit hash in status.md"
   git push origin main
   ```
4. Deliver handoff summary: **Completed 6 / 9; Remaining: 3**.

## 8. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA05: Sensory Moment Vault on branch main.

Pre-flight (run first, paste output):
  git branch --show-current
  git status --short

Read docs/hwga/README.md, docs/hwga/trd.md, docs/hwga/contracts.md, docs/hwga/implementation.md, docs/hwga/status.md, the existing storage/API/client code, and phases/HWGA05_sensory_moment_vault.md. Inspect Git state and current code before editing.

Implement only user-initiated photo, 5-10 s ambient audio, and voice-scrap capture plus authenticated local-media upload/retrieval/deletion — per contracts.md (MediaAssetMeta, MediaKind, TranscriptState, /media routes). Bytes on backend-controlled local disk; metadata in Postgres. Validate all server-side properties; generated opaque paths; owner checks and limits from the HWGA01 media decision. Flutter uses the API and must not learn server filesystem paths. No static mount, no logging private content, no cloud media service, no raw media to Gemini. Follow the recorded transcription decision and include the MANUAL_TEXT fallback.

Write and run:
  cd backend && uv run pytest tests/test_media.py -q -ra
  cd flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test
Test unauthenticated access, ownership, malformed MIME, excessive bytes/duration, and cleanup. A check that was not run counts as failed. Full app regression remains HWGA08.

Finish with the Two-Step Commit Protocol exactly as written in the phase file (implementation commit → hash → status.md docs commit → git push origin main). Report both commit hashes. Stop before HWGA06.
```

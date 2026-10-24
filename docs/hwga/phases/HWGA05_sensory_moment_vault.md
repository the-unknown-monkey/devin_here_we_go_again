# Phase HWGA05: Sensory Moment Vault

- **Status:** Planned
- **Dependency:** HWGA02 storage/auth foundation and HWGA03 phone connection
- **Scope:** Raw photos, ambient audio, voice scraps, private media lifecycle

## 1. Goal

Let the user preserve sensory moments without turning capture into a public or performative post. Implement a private, authenticated media round trip with safe local storage.

## 2. Deliverables

- Flutter raw photo capture/pick flow with camera permission requested at point of use.
- Ambient sound recording capped at 5-10 seconds as specified in HWGA01; show recording state and duration.
- Voice scrap recording with text/transcript fallback; respect the approved transcription/provider decision.
- Authenticated backend upload and playback/download/delete routes.
- Metadata persistence for owner, media kind, captured time, MIME, byte length, audio duration, transcript state, and opaque storage key.
- Backend storage adapter enforces generated filenames, path confinement, accepted content types, upload size, duration, ownership, and deletion behavior.
- Timeline cards for image/audio/voice with playback and understandable permission/network/storage errors.
- `.gitignore` protection for local media and tests for unauthorized access, invalid content, size/duration limits, and safe deletion.

## 3. Privacy Boundaries

- Never mount local media as a public static directory.
- Never trust client filenames, MIME values, filesystem paths, or ownership ids.
- Do not send raw media to Gemini in this phase. Transcription must follow HWGA01 and must not expose credentials.
- Do not log transcripts or signed/private media URLs.

## 4. Exit Criteria

- A phone-created sample can be uploaded, fetched by its owner, played/viewed, and deleted.
- Another unauthenticated/unauthorized request cannot access that media.
- Focused limit/validation tests and capture widget checks pass; record actual output.

## 5. Copy-Paste Prompt for a New Chat

```text
Please execute Phase HWGA05: Sensory Moment Vault.

Read docs/hwga/README.md, docs/hwga/trd.md (especially service boundaries/privacy), docs/hwga/implementation.md, docs/hwga/status.md, accepted HWGA01 media/transcription decisions, existing storage/API/client code, and this phase file. Inspect Git state and current code before editing.

Implement only the user-initiated photo, 5-10 second ambient audio, and voice-scrap capture plus authenticated local-media upload/retrieval/deletion. Keep bytes on backend-controlled local disk and metadata in Postgres. Validate all server-side properties; use generated opaque paths; enforce owner checks and limits. Flutter must use the API and must not learn server filesystem paths. Do not expose media statically, log private content, add cloud media services, or send raw media to Gemini. Follow the recorded transcription decision and include a manual text fallback.

Preserve unrelated work and limit edits to this phase. Add/run focused security/storage/capture checks; test unauthenticated access, ownership, malformed MIME, excessive bytes/duration, cleanup, and expected audio playback behavior as applicable. Full app regression remains HWGA08. Report exact verification evidence and limitations; update status with actual results only. No commit/push. Stop before HWGA06.
```

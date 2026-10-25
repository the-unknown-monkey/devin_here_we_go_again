# HWGA Runbook — Verified V1 Operations

- **Created:** 2026-10-25, Asia/Kolkata — after HWGA08 V1 acceptance on Nothing Phone 2a
- **Rule:** every command below was actually executed and verified during HWGA08. No invented commands, no secrets/tokens.
- **Environment:** Windows 11, Python 3.13.11, uv 0.11.13, Flutter 3.41.1/Dart 3.11.0, Docker 29.1.2 (Postgres 17-alpine), ngrok 3.39.11, Nothing Phone 2a (`model:A142`, serial `000563429001789`, Android 15).
- **Ports (locked, with HWGA02 user-approved substitutes):** API `127.0.0.1:8000`; dev Postgres `127.0.0.1:55532`; disposable test Postgres `127.0.0.1:55533` (tmpfs).

## 1. Start the stack

```powershell
cd backend
docker compose up -d db          # dev Postgres on 127.0.0.1:55532
docker compose up -d db-test     # disposable test DB on 127.0.0.1:55533 (tmpfs)
uv run alembic upgrade head      # current head: 5e1d2551dffb
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
curl http://127.0.0.1:8000/health   # -> {"status":"ok"}
```

`backend/.env` (gitignored) must contain `DATABASE_URL`, `MEDIA_STORAGE_ROOT`, `AUTH_TOKEN_PEPPER`, `USER_TIMEZONE`, and `GEMINI_API_KEY` for live generation. `GEMINI_MODEL` optional (default `gemini-3.5-flash`, verified ~9.8s structured output; `gemini-3.8`/`3.6` were demand-limited, `3.7` exceeded the 20s timeout).

## 2. Test suites (disposable data only)

```powershell
cd backend && uv run pytest tests -q -ra          # 97 passed (HWGA08)
cd ..\flutter && dart format --set-exit-if-changed lib test && flutter analyze && flutter test   # clean, 35 passed
```

Tests pin `TEST_DATABASE_URL` (55533, tmpfs) and refuse to run if it equals `DATABASE_URL`. Never point them at dev data.

## 3. Phone over USB (D15 dev route)

```powershell
%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe devices        # expect A142 "device"
%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe reverse tcp:8000 tcp:8000
%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe reverse --list # expect UsbFfs tcp:8000 tcp:8000
cd flutter && flutter build apk --debug && flutter install -d 000563429001789 --debug
```

- App default base URL `http://127.0.0.1:8000` reaches the host through the reverse tunnel. Use `127.0.0.1`, not `localhost` (phone resolver rejected it).
- **`adb reverse` is wiped whenever the device disconnects** (replug, `adb kill-server`). Symptom on the phone: "Connection refused" — re-run the reverse command.
- `adb` may not be on PATH; invoke it via the platform-tools path above.

## 4. Phone over ngrok (demo route — approved, authenticated only)

```powershell
ngrok http 8000
curl http://127.0.0.1:4040/api/tunnels     # read public_url (do not commit it)
cd flutter && flutter build apk --debug --dart-define=HWGA_API_BASE_URL=<public_url>
flutter install -d 000563429001789 --debug
```

Verified security posture during HWGA08 — re-verify every tunnel:

- `/health` → 200 (unauthenticated by design)
- `/me` without token → `401 UNAUTHORIZED`; with wrong token → 401
- `/docs`, `/openapi.json` → 404 (disabled)
- Only port 8000 is tunneled. Postgres is bound `127.0.0.1` only and is never exposed.
- Free-tier ngrok can throw transient 5xx on a request; app-level retries cover it.
- Fortinet TLS interception on this network blocked the ngrok dashboard during HWGA00; the tunnel itself worked on 2026-10-25.

**Shut the tunnel down when done** (`Ctrl+C` on the ngrok process). Treat the public URL as hostile ingress — never disable auth, never tunnel Postgres or Docker.

## 5. Auth token lifecycle (D07)

```powershell
cd backend && uv run python -m app.cli provision-token
```

Prints the bearer token once; stores only the HMAC-SHA256+pepper hash. Enter it on the phone's token screen — it lives in Android Keystore via `flutter_secure_storage`. Reinstalling the app wipes it: provision again and re-enter (rotation = re-run CLI).

## 6. Generation triggers

- `GET /recaps?period=DAILY&date=YYYY-MM-DD` — generates on first fetch; regenerates once when a backfilled event (`occurred_at` before the recap's `created_at`) marks it stale.
- `GET /recaps?period=WEEKLY&date=YYYY-MM-DD` — weekly roll-up over stored dailies.
- `GET /directive/today` — generates once per `(user, for_date)`; `shown_at` dedupes display. Never regenerates same-day by design.
- `POST /internal/run/daily` · `POST /internal/run/weekly` — authenticated job triggers. `monthly`/`yearly` → honest 404 (post-V1).
- All provider calls: ≤2 retries, timeout-bounded; exhaustion → deterministic `FALLBACK` persisted; fact/chain guards reject unsupported claims → `FALLBACK`. `FAILED` only for observable persistence errors.

## 7. Safe shutdown

```powershell
# stop ngrok (Ctrl+C on its console)
taskkill //PID <pid-on-8000> //F     # find via: netstat -ano | findstr 127.0.0.1:8000
cd backend && docker compose stop   # or `down` to remove (data volume persists)
```

Note: `pkill -f uvicorn` did not reliably kill the server on Windows during HWGA08 — kill by port PID.

## 8. Troubleshooting observed during HWGA08

| Symptom | Cause | Fix |
|---|---|---|
| Phone: "Connection refused" | `adb reverse` mapping dropped on reconnect | re-run `adb reverse tcp:8000 tcp:8000` |
| Uvicorn won't start (WinError 10048) | old process still holds port 8000 | kill PID from `netstat -ano` |
| Receipt stuck `FALLBACK`, log `kind=NO_KEY` | server started before `GEMINI_API_KEY` was added | restart uvicorn |
| `INVALID_OUTPUT` from provider | thinking tokens consumed `max_output_tokens` (was 1500) | fixed in code — now 8192 |
| Gemini 404/503 on model | upstream deprecation / demand spike | set `GEMINI_MODEL` to a verified name (`gemini-3.5-flash`) |
| `adb`/`flutter` not found in a new shell | PATH not refreshed | use absolute paths (`platform-tools\adb.exe`, `C:\src\flutter\bin`) |

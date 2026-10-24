# Here We Go Again (HWGA) — Development Documentation & Architecture Blueprint

> **Hackathon Track:** *Make the Invisible Visible* — build something that helps people notice what they normally miss, and do something useful with that information.

---

## 1. Project & Git Details

| Field | Value |
|---|---|
| Project name | **Here We Go Again (HWGA)** |
| Repository | `devin_here_we_go_again` |
| Remote (origin) | `https://github.com/the-unknown-monkey/devin_here_we_go_again.git` |
| Default branch | `main` |
| Remote setup | `git remote add origin https://github.com/the-unknown-monkey/devin_here_we_go_again.git` |
| Platform target | Android (Flutter) |
| Backend | FastAPI (Python) |
| Agentic layer | LangChain + LangGraph (Python) with a **Gemini Thinking Node** |
| Version | v1 (hackathon scope) |

---

## 2. Product Overview

### 2.1 What are we building?

HWGA is a **private, single-player social feed built strictly for yourself** — "social media for one." Zero followers, zero likes, zero flexing. It captures the invisible micro-moments of a person's day (physical care, rest, sudden ideas, ambient sights and sounds) and uses an agentic LangChain/Gemini pipeline to turn those invisible patterns into **self-awareness and real next-day action**.

### 2.2 Why are we building it?

Modern platforms are broken:

- **LinkedIn** is flooded with fake motivation, fake stories, and performative hustle.
- **Instagram** is flooded with show-off culture and a masked life.
- People live on repetitive autopilot: forgetting their real ideas by the next morning, losing touch with physical health (sitting for hours without stretching, bad food, silent burnout), impulse buying out of boredom, and numbing out with cheap dopamine because they feel empty.

Humans easily forget who they were yesterday, lose their 2 AM sparks by 9 AM, and miss the tiny daily habits silently ruining — or building — their health and purpose. HWGA makes those invisible micro-moments visible, then does something useful with them.

### 2.3 Who is it for?

- Individuals who feel their weeks blur together ("where did my week go?").
- Desk workers / builders / students whose bodies decay silently at a desk.
- People who have ideas at 2 AM that evaporate by morning.
- Anyone tired of performative social media who wants a private space that serves *them*, not an algorithm.

### 2.4 Desired outcome

By the end of every day, week, and month, the user gets **two undeniable results**:

1. **Emotional & sensory proof** — a smile on their face because they can *see and hear* that their life isn't an empty blur. Even a quiet, rainy Sunday counts as quality lived time.
2. **Behavioral & physical shift** — real improvements in posture, hydration, food, focus, and bucket-list execution, because the LangChain + Gemini pipeline catches what they miss at night and guides their next morning.

### 2.5 Core philosophy

1. **"You Are Your Own Audience"** — nobody cares about your life as much as you must. Algorithms want your attention, not your well-being. HWGA is strictly private.
2. **"Have as much fun as you want, and after that put your 100%"** — we reject toxic hustle guilt. A "Slow Sleepy Sunday" enjoyed 100% is a win; locked-in work gets 100%. No gray-zone zombie drifting.
3. **"Make the Invisible Visible"** — capture micro-moments and hidden drift, surface them honestly, and convert them into action.

---

## 3. V1 Feature Specification

### 3.1 The 5 Human Baselines

Instead of corporate KPIs, v1 tracks and protects five real human fundamentals:

| # | Baseline | What it means | Signals captured |
|---|----------|---------------|------------------|
| 1 | **Clean & Healthy Fuel** | Real food and regular water vs. boredom/junk eating | Meal confirmations, water intake taps |
| 2 | **Healthy, Moving Body** | Stretching, posture resets, walking; breaking long seated chains | Stretch/posture/walk confirmations |
| 3 | **Peace of Mind** | Quiet moments away from high-dopamine noise | Quiet-moment logs, ambient capsules |
| 4 | **Guilt-Free Rest ("Slow Sleepy Sunday" mode)** | Intentional recovery, naps, leisure — a positive win, not laziness | Rest mode state, leisure logs |
| 5 | **100% Locked-In Effort** | Pure, focused blocks building, working, or growing | Locked-in mode state, focus-block durations |

### 3.2 The Sensory Moment Vault

User-initiated memory capsules dropped into the private timeline to defeat time-blindness:

- **Raw Snaps** — quick photos of surroundings, food, desk, sky, walk. No filters, no public captions.
- **Ambient Sound Capsules (5–10s)** — real sounds: rain, cafe chatter, birds, quiet room, keyboard clicks. Playback later = mentally traveling back to that exact moment.
- **Voice Scraps & 2 AM Sparks** — sudden ideas, thoughts, feelings dumped before they evaporate by morning. Transcribed for the pipeline.

### 3.3 Micro-Confirmations & Routine Pulse

- **Quick Reality Confirmations** — low-friction 1-tap prompts: "Did you stretch? Fix your posture? Drink water? Walk? Eat clean today?"
- **Mode State** — the user is always in one of two modes: **100% Locked-In** or **Pure Fun / Recovery**. The mode log feeds the pipeline so rest is credited, not judged.

### 3.4 The "Rule of 3" Aging Bucket List

- **Strict 3-slot cap** — maximum 3 active life/personal ideas or bucket-list goals at a time. No 50-item graveyard of forgotten dreams.
- **Visible aging** — each item shows days elapsed since it was added; procrastination becomes visible.
- **Unlock rule** — a new idea can only be added when one of the 3 is completed or consciously retired.

---

## 4. System Architecture

### 4.1 High-level components

```
┌────────────────────┐        ┌─────────────────────────┐        ┌──────────────┐
│  Flutter Android   │ HTTPS  │   FastAPI Backend        │        │   Gemini     │
│  (camera, mic,     │───────▶│  - REST API              │        │  (multimodal │
│   timeline UI,     │        │  - LangChain/LangGraph   │───────▶│   reasoning  │
│   media playback)  │        │    pipeline orchestrator │        │   node)      │
└────────────────────┘        │  - Scheduled recap jobs  │        └──────────────┘
                              └───────────┬─────────────┘
                                          │
                    ┌─────────────────────┼──────────────────────┐
                    ▼                     ▼                      ▼
            ┌──────────────┐      ┌──────────────┐       ┌──────────────┐
            │  Postgres    │      │  Object      │       │  Push notif. │
            │  (events,    │      │  storage     │       │  (FCM) for   │
            │   recaps,    │      │  (snaps,     │       │  morning     │
            │   bucket list)│     │  audio,      │       │  directives  │
            └──────────────┘      │  voice)      │       └──────────────┘
                                  └──────────────┘
```

### 4.2 Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Mobile app | **Flutter (Android)** | Camera, mic recording, local cache/offline queue, timeline UI, audio playback |
| Backend API | **FastAPI (Python)** | Event ingestion, media upload, recap/directive retrieval |
| Agentic orchestration | **LangChain + LangGraph (Python)** | Stateful pipeline graphs; deterministic routing between aggregate → reason → persist → emit |
| LLM reasoning | **Gemini (Thinking Node)** | Multimodal reasoning over daily context; narrative + structured-insight generation |
| Database | **Postgres** (e.g., Supabase or plain Postgres + SQLAlchemy) | Events, recaps, bucket list |
| Media storage | **Object storage** (S3-compatible / Supabase Storage / GCS) | Snaps, ambient audio, voice scraps; DB stores refs |
| Scheduling | **APScheduler / Celery Beat / cron endpoint** | Triggers nightly, weekly, monthly, yearly pipelines |
| Push notifications | **Firebase Cloud Messaging** | Morning Directive delivery |
| Speech-to-text | **Gemini audio / Whisper** | Transcribing voice scraps for the pipeline |

### 4.3 Request/flow summary

1. App captures an event (confirmation tap, mode toggle, snap, audio capsule, voice scrap) → uploads media to object storage → posts event + media ref to FastAPI.
2. FastAPI writes to the **Raw Event Log Store**.
3. Scheduled jobs (nightly, weekly, monthly, yearly) run LangGraph pipelines that read the appropriate inputs, invoke the Gemini Thinking Node, and persist structured recaps.
4. App fetches recaps + the next Morning Directive and renders the private "Proof of Life" chronicle.

---

## 5. Agentic Pipeline Architecture (LangChain / LangGraph + Gemini)

We are not just storing logs — an **agentic workflow** turns invisible patterns into real, actionable results. Both pipelines share a common shape: **Aggregate → Reason (Gemini Thinking Node) → Persist → Emit**.

### 5.1 Pipeline 1 — Daily Ingestion & the "Nightly Unvarnished Receipt"

**Trigger:** scheduled nightly job (user-local evening) or manual "close my day" tap.

**Inputs (today's raw events):**
- Physical confirmations: water, stretch, posture, walk, food
- Mode logs: 100% locked-in vs. guilt-free rest (with durations)
- Voice scraps / 2 AM ideas (transcripts)
- Sensory snaps metadata (timestamps, tags)
- Active Rule-of-3 bucket list status + ages

**Step 1 — LangChain State Aggregator:** normalizes all daily events into a structured `DailyContext` object:

```json
{
  "date": "2026-10-24",
  "physical": { "water": 3, "stretch": true, "posture_resets": 2, "walk_min": 0, "clean_meals": 2 },
  "modes": [{ "mode": "locked_in", "start": "09:12", "end": "15:40" }, { "mode": "rest", "start": "20:00", "end": "23:00" }],
  "ideas": [{ "id": "v9", "transcript": "app that reminds me to call grandma", "captured_at": "02:14" }],
  "media_refs": ["snap://a1", "audio://r2"],
  "bucket_list": [{ "id": "b2", "title": "learn to swim", "age_days": 21, "action_today": false }]
}
```

**Step 2 — Gemini Thinking Node (reasoning):**
- Correlates physical care with mental state (e.g., "You worked 6 hours straight without stretching or water" OR "You took a full Slow Sleepy Sunday with rain audio snaps and zero work guilt").
- Checks whether any 2 AM ideas were captured so they don't get forgotten.
- Checks whether the 3 bucket-list items are aging without action.

**Step 3 — Output (persisted as `DAILY_RECAP`):** a grounded, honest **Nightly Receipt** — proving the user lived a real day, celebrating either their 100% effort or their quality rest, and highlighting what they would normally have missed.

### 5.2 Pipeline 2 — Next-Morning Action Generator ("The Morning Directive")

**Trigger:** morning (scheduled or on first app open after wake).

**Inputs:** last night's stored `DAILY_RECAP` + recent historical context (recent daily recaps, bucket list state).

**Gemini Thinking Node:** reasons about what the user needs *today* based on *yesterday's* invisible gaps.

**Output (`directive_for_today`):** a concrete, personalized nudge + focus plan, e.g.:
- Resurface a 2 AM idea they would have forgotten.
- Adjust today's stretch/water priority because yesterday was heavy.
- Push one of the 3 aging bucket-list items.

Delivered via FCM push + shown at top of the feed.

---

## 6. Multi-Tier Recap Architecture (Storage & Pipeline Chaining)

### 6.1 Storage model — Hierarchical Memory Compaction

We never re-read thousands of raw logs for long windows. Two stores:

1. **Raw Event Log Store** — individual snaps, audio file refs, voice transcripts, 1-tap confirmations, all timestamped.
2. **Structured Recap Store (`recaps` table)** — every recap (`DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`) stored as:

| Field | Type | Contents |
|---|---|---|
| `id` | uuid | recap id |
| `user_id` | uuid/fk | owner |
| `period_type` | enum | `DAILY` \| `WEEKLY` \| `MONTHLY` \| `YEARLY` |
| `period_start` / `period_end` | date | window |
| `summary_narrative` | text | the human story of that period |
| `extracted_insights` | jsonb | hidden patterns, energy leaks, health compliance, mood shifts |
| `highlight_media_refs` | jsonb | pointers to the best snaps, ambient sounds, voice notes in the window |
| `directive_for_next_cycle` | text | what the next pipeline should act on |
| `created_at` | timestamp | generation time |

### 6.2 Pipeline chaining — Map-Reduce Memory

Each tier consumes the **previous tier's recaps**, not raw logs:

| Pipeline | Consumes | Produces | Detects |
|---|---|---|---|
| **Daily** | today's raw event logs | `DAILY_RECAP` → feeds Morning Directive | daily gaps, forgotten ideas |
| **Weekly** | 7 stored `DAILY_RECAP`s | `WEEKLY_RECAP` + curated weekly snaps/sounds | multi-day drift ("started clean, crashed Thursday, ignored bucket item #2") |
| **Monthly** | 4 stored `WEEKLY_RECAP`s + bucket-list history | `MONTHLY_RECAP` | macro lifestyle shifts, forgotten hobbies, real progress |
| **Yearly** | 12 stored `MONTHLY_RECAP`s | `YEARLY_RECAP` | the ultimate "Proof of a Lived Year" chronicle |

### 6.3 How recaps are shown

Rendered as a private, non-comparative **"Proof of Life" Story/Chronicle** in the personal feed — combining the Gemini narrative with the user's actual photos, ambient audio playback, and voice scraps from that day/week/month/year. No streaks-vs-others, no comparison, no metrics-shaming.

---

## 7. Data Model (v1 draft)

```
users            (id, created_at, timezone, fcm_token)
events           (id, user_id, type, payload jsonb, occurred_at)
                   -- type: confirmation | mode_toggle | snap | audio_capsule
                   --      | voice_scrap | quiet_moment
media_assets     (id, user_id, kind [image|audio], storage_uri, duration_sec,
                  transcript?, captured_at)
bucket_items     (id, user_id, title, status [active|done|retired],
                  created_at, resolved_at)   -- enforce ≤ 3 active per user
recaps           (id, user_id, period_type, period_start, period_end,
                  summary_narrative, extracted_insights jsonb,
                  highlight_media_refs jsonb, directive_for_next_cycle,
                  created_at)
directives       (id, user_id, for_date, content, delivered_at)
```

Invariants enforced at the API layer:
- `bucket_items.active ≤ 3` per user — insert rejected until one is completed/retired.
- `events.type` constrained to the enum above.
- Voice scraps always produce a `media_assets.transcript` before the nightly run.

---

## 8. Draft API Surface (FastAPI)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/events` | ingest confirmation / mode toggle / quiet moment |
| `POST` | `/media` | upload snap or audio capsule (multipart) → returns `media_asset_id` |
| `GET`  | `/timeline?from=&to=` | private feed: events + media refs |
| `GET`  | `/mode` · `POST /mode` | current mode state |
| `GET`  | `/bucket` · `POST /bucket` | list (with ages) / add (enforces 3-cap) |
| `POST` | `/bucket/{id}/complete` · `/bucket/{id}/retire` | resolve item, freeing a slot |
| `GET`  | `/recaps?period=DAILY&date=` | fetch a recap |
| `GET`  | `/directive/today` | today's Morning Directive |
| `POST` | `/internal/run/{daily\|weekly\|monthly\|yearly}` | scheduler-invoked pipeline triggers (auth-guarded) |

---

## 9. Hackathon Build Order (Suggested Milestones)

1. **M0 — Skeleton:** Flutter app shell, FastAPI server, Postgres schema, object storage, GitHub repo hygiene (`.gitignore`, env handling).
2. **M1 — Capture:** 1-tap confirmations, mode toggle, Rule-of-3 bucket list with aging display.
3. **M2 — Vault:** raw snaps, 5–10s audio capsules, voice scraps + transcription.
4. **M3 — Nightly Receipt:** DailyContext aggregator → Gemini node → `DAILY_RECAP` + receipt UI.
5. **M4 — Morning Directive:** pipeline 2 + FCM push.
6. **M5 — Chained recaps:** weekly (then monthly/yearly if time) + "Proof of Life" chronicle view.

---

## 10. Risks & Open Questions

- **Auth:** simplest viable auth for v1 (single-user hackathon? Supabase Auth? device-key?). Needs a decision before media upload ships.
- **Timezones:** nightly/weekly jobs must run in *user-local* time, not server time.
- **Gemini cost/latency:** recap prompts must be compact (pass `DailyContext`, not raw dumps); consider caching weekly inputs.
- **Notifications:** FCM required for Morning Directive; fallback = in-app banner on first open.
- **Media quota:** snaps/audio grow fast; set retention or compression policy.
- **Privacy posture:** everything is private-by-design; no social graph, ever. Document this as a hard product invariant.

---

*This document is the foundation for HWGA v1. Application code should not diverge from it without updating this file first.*

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
| Primary acceptance device | **Nothing Phone 2a (Android)** |
| Current development branch | `main` |

> Source code belongs in `flutter/` and `backend/`. The authoritative technical contracts, implementation map, status ledger, and copy-ready phase prompts are indexed in [`docs/hwga/README.md`](docs/hwga/README.md).

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
- **Target age group:** people approximately **20-35 years old**. This is an audience age range, not a user-count target or an age restriction.

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

### 3.5 V1 UI/UX Baseline

V1 uses a **minimal, clean, modern Android interface** that feels calm, personal, and easy to use. Prioritize clear hierarchy, readable typography, consistent icons, restrained color, and purposeful transitions/animations for navigation, capture feedback, and recap reveal. Respect Android accessibility settings, including reduced motion where practical. V1 is a coherent usable product, not a major visual redesign. Test the complete v1 on the user's **Nothing Phone 2a** before beginning substantial UI/UX refinement or adding nonessential features.

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
            │  Postgres    │      │  Local disk  │       │  In-app      │
            │  (events,    │      │  media store │       │  Morning     │
            │   recaps,    │      │  (snaps,     │       │  Directive   │
            │   bucket list)│     │  audio,      │       │  delivery    │
            └──────────────┘      │  voice)      │       └──────────────┘
                                  └──────────────┘
```

The Gemini model may support multimodal input, but the v1 privacy default is structured text/transcript context only; raw photos/audio are not sent to the model.

### 4.2 Tech stack

| Layer | Choice | Notes |
|---|---|---|
| Mobile app | **Flutter (Android)** | Camera, mic recording, local cache/offline queue, timeline UI, audio playback |
| Backend API | **FastAPI (Python)** | Event ingestion, media upload, recap/directive retrieval |
| Agentic orchestration | **LangChain + LangGraph (Python)** | Stateful pipeline graphs; deterministic routing between aggregate → reason → persist → emit |
| LLM reasoning | **Gemini (Thinking Node)** | Server-side narrative and structured-insight generation from validated context; raw media is not sent by default |
| Database | **Postgres in Docker** | Local hackathon database; data access through backend repositories |
| Media storage (hackathon) | **Local filesystem behind the backend** | Database stores metadata and relative storage keys; authenticated API serves media. Never expose the storage directory directly. |
| Scheduling | **APScheduler or explicit in-app trigger** | Keep local hackathon scheduling simple and idempotent; use the user's local timezone. |
| Directive delivery (v1) | **In-app** | Show the Morning Directive on app open; defer FCM until after v1 acceptance. |
| Speech-to-text | **Backend transcription adapter** | Provider is finalized in HWGA01; preserve a manual-text fallback. |
| Demo tunnel | **ngrok on Windows 11** | Expose only the authenticated FastAPI port when needed; never expose Postgres. |

### 4.3 Request/flow summary

1. App posts confirmations/mode events to FastAPI. For a sensory moment, it uploads media through the authenticated API; the backend stores bytes on private local disk and persists only metadata/storage keys in Postgres.
2. FastAPI writes to the **Raw Event Log Store**.
3. Idempotent daily/weekly jobs (or an explicit in-app trigger for the local MVP) run LangGraph workflows that read the appropriate inputs, invoke the Gemini Thinking Node, and persist structured recaps. Monthly/yearly generation is deferred until after V1 acceptance unless scope is explicitly changed.
4. App fetches recaps + the next Morning Directive and renders the private "Proof of Life" chronicle. V1 delivery is in-app; Firebase push is deferred.

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
- Describes only recorded relationships between physical-care events, mode logs, rest, and captured moments (e.g., "You logged a six-hour focus block without a water confirmation" or "You chose recovery and captured the rain"). It must not infer an unrecorded mental state or claim causation.
- Checks whether any 2 AM ideas were captured so they don't get forgotten.
- Checks whether the 3 bucket-list items are aging without action.

**Step 3 — Output (persisted as `DAILY_RECAP`):** a grounded, honest **Nightly Receipt** — proving the user lived a real day, celebrating either their 100% effort or their quality rest, and highlighting what they would normally have missed.

### 5.2 Pipeline 2 — Next-Morning Action Generator ("The Morning Directive")

**Trigger:** first app open on a new local date for v1; a background schedule is deferred unless HWGA01 explicitly selects and verifies one.

**Inputs:** last night's stored `DAILY_RECAP` + recent historical context (recent daily recaps, bucket list state).

**Gemini Thinking Node:** reasons about what the user needs *today* based on *yesterday's* invisible gaps.

**Output (`directive_for_today`):** a concrete, personalized nudge + focus plan, e.g.:
- Resurface a 2 AM idea they would have forgotten.
- Adjust today's stretch/water priority because yesterday was heavy.
- Push one of the 3 aging bucket-list items.

Shown in-app at the top of the private feed. Firebase push notifications are deferred until after v1 acceptance.

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
| `extracted_insights` | jsonb | evidence-backed patterns, energy leaks, baseline signals; mood shifts only if explicitly logged in a future approved feature |
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

The architecture supports all four tiers. The v1 implementation prioritizes Daily and Weekly; Monthly and Yearly generation are post-v1 work unless the user explicitly expands the accepted scope.

### 6.3 How recaps are shown

Rendered as a private, non-comparative **"Proof of Life" Story/Chronicle** in the personal feed — combining the Gemini narrative with the user's actual photos, ambient audio playback, and voice scraps from that day/week/month/year. No streaks-vs-others, no comparison, no metrics-shaming.

---

## 7. Data Model (v1 draft)

```
users            (id, created_at, timezone)
events           (id, user_id, type, payload jsonb, occurred_at)
                   -- type: confirmation | mode_toggle | snap | audio_capsule
                   --      | voice_scrap | quiet_moment
media_assets     (id, user_id, kind [image|audio], storage_key, duration_sec,
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
- Voice scraps have a transcript or an explicit pending/failed transcription state; a transcription outage must not block daily recap generation.

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
| `POST` | `/internal/run/{daily\|weekly}` | internal, authenticated v1 job trigger; monthly/yearly routes are future scope |

---

## 9. Hackathon Build Order

The implementation is divided into auditable phases. The phase guide and copy-ready prompts are in [`docs/hwga/phases/`](docs/hwga/phases/).

1. **HWGA00 — Setup & environment verification:** audit/install required tools and verify Flutter, Android USB debugging, Python, Docker/Postgres, and ngrok wiring.
2. **HWGA01 — Decision contracts:** freeze v1 scope, privacy and AI rules, data/API contracts, timezone behavior, and implementation choices.
3. **HWGA02 — Backend foundation:** FastAPI structure, local Postgres, migrations, single-user auth, event/media interfaces, health endpoint, and isolated test database.
4. **HWGA03 — Flutter foundation & connection:** app shell, API client, configuration, permissions, and first authenticated phone-to-backend request.
5. **HWGA04 — Human baselines & Rule of 3:** confirmations, mode transitions, private timeline, aging goals, and server-enforced three-active-item cap.
6. **HWGA05 — Sensory Moment Vault:** raw photos, 5-10 second ambient recordings, voice scraps, private local media storage, and transcript fallback.
7. **HWGA06 — Daily Receipt:** deterministic event aggregation, typed recap contract, Gemini narrative, fallback, fact guard, and receipt screen.
8. **HWGA07 — Morning Directive & recap chain:** in-app next-day directive and weekly recap/chronicle. Monthly/yearly recap contracts are designed for v1; full implementation is post-v1 unless the scope is explicitly changed.
9. **HWGA08 — Final v1 acceptance:** full regression and end-to-end gate, Nothing Phone 2a acceptance, ngrok demo verification, and user-approved runbook evidence.
10. **Post-v1 — Product refinement:** use real phone-test feedback to refine UI/UX and prioritize additional features without destabilizing the accepted baseline.

---

## 10. Risks & Open Questions

- **Auth:** single-user private auth is selected; HWGA01 locks the credential provisioning/session mechanism before protected media endpoints ship.
- **Timezones:** nightly/weekly jobs must run in *user-local* time, not server time.
- **Gemini cost/latency:** recap prompts must be compact (pass `DailyContext`, not raw dumps); consider caching weekly inputs.
- **Notifications:** Morning Directive is in-app for v1; FCM is deferred.
- **UI/UX scope:** v1 has a minimal, clean, modern visual baseline with purposeful motion and consistent icons; major redesign is post-acceptance.
- **Media quota:** snaps/audio grow fast; set retention or compression policy.
- **Privacy posture:** everything is private-by-design; no social graph, ever. Authenticate all media access, keep secrets out of source control, and never expose Postgres through ngrok.

---

*This document is the foundation for HWGA v1. Application code should not diverge from it without updating this file first.*

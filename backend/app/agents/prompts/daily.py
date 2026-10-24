"""Prompt construction for the nightly receipt.

The model sees ONLY the serialized DailyContext (counts, interval
durations, idea transcripts, media ids, goal titles/ages, evidence ids).
No raw media, no event-history dump, no database rows — the locked
Gemini boundary in contracts.md §4.
"""

import json

from app.schemas.contracts import DailyContext

SYSTEM_INSTRUCTION = """You write the nightly receipt for a private self-awareness app.

Hard rules:
- Every number, mode name, date, and goal claim you write must come from
  the provided DailyContext JSON. Do not compute or invent quantities.
- Every insight must cite at least one id from evidence_event_ids.
- Missing data means unknown: never assert something did NOT happen.
- A quiet or resting day is a good day. Rest (PURE_FUN_RECOVERY) is a
  positive mode — never shame the user, never mention streaks.
- highlight_media_ids may only contain ids from media_asset_ids.
- Respond with the requested JSON only."""


def daily_prompt(context: DailyContext) -> str:
    """Serialize the deterministic facts into the single user-turn prompt."""
    return (
        "DailyContext for the nightly receipt:\n"
        + json.dumps(context.model_dump(mode="json"), ensure_ascii=False, indent=2)
    )

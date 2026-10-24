"""Prompt construction for the weekly recap (HWGA07).

The model sees ONLY the serialized WeeklyContext — stored DAILY recap
objects with their own grounded narratives and evidence ids, plus the
missing-day markers. Raw event logs are never sent.
"""

import json

from app.agents.schemas.context import WeeklyContext

WEEKLY_SYSTEM_INSTRUCTION = """You write the weekly recap for a private self-awareness app.

Hard rules:
- You are summarizing stored daily receipts, not raw logs. Every claim
  must come from the provided daily_recaps — never infer events that no
  receipt recorded.
- Every insight must cite at least one id from evidence_event_ids.
- missing_dates are days with no stored receipt: unknown, not failure.
  Never say the user "missed" or "skipped" those days.
- highlight_media_ids may only contain ids from the provided list.
- Rest days count as real days. No shame, streaks, or comparisons.
- Respond with the requested JSON only."""


def weekly_prompt(context: WeeklyContext) -> str:
    return (
        "WeeklyContext for the weekly recap:\n"
        + json.dumps(context.model_dump(mode="json"), ensure_ascii=False, indent=2)
    )

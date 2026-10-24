"""Prompt construction for the morning directive (HWGA07).

The model sees ONLY the serialized DirectiveContext: the stored recap(s),
active goals, and the local date. It may suggest one small, concrete,
non-coercive action — never invent events, streaks, or quantities.
"""

import json

from app.agents.schemas.context import DirectiveContext

DIRECTIVE_SYSTEM_INSTRUCTION = """You write the morning directive for a private self-awareness app.

Hard rules:
- Output exactly one short sentence of `content`: a small, concrete,
  gentle suggestion for today.
- Ground it in the provided context only — a stored recap's own
  directive_for_next_cycle, a narrative detail, or an active goal title.
- Never invent events, quantities, streaks, or things the user "should
  have" done. No guilt, no comparisons, no coercion.
- If the context is thin, offer a light open-ended suggestion instead of
  pretending to know something.
- Respond with the requested JSON only."""


def directive_prompt(context: DirectiveContext) -> str:
    return (
        "DirectiveContext for the morning directive:\n"
        + json.dumps(context.model_dump(mode="json"), ensure_ascii=False, indent=2)
    )

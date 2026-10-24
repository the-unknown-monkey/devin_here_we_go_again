"""Deterministic guards and fallbacks for the recap chain (HWGA07).

Same contract as the daily fact guard: the model proposes, code disposes.

Weekly rules:
- insights must cite ids from the union of evidence_event_ids carried by
  the stored daily recaps; highlight_media_ids must be a subset of the
  media the daily recaps referenced
- quantity claims ("N days", "N receipts") must equal the computed
  coverage or appear verbatim inside a source recap's text — the model
  cannot infer anything the receipts did not record
- missing days are unknown, never failure; shame/coercion rejects the
  candidate

Directive rules:
- one short line, no shame/coercion/comparison
- digits are allowed only if they appear verbatim inside a goal title or
  the stored recap text they were grounded in
"""

import re
import uuid
from dataclasses import dataclass

from app.agents.fact_guard import _SHAME
from app.agents.schemas.context import DirectiveContext, WeeklyContext
from app.agents.schemas.directive import DirectiveCandidate
from app.agents.schemas.receipt import RecapCandidate

_COERCE = re.compile(
    r"\b(you must|you have to|no excuses?|should have|ought to|stop being|"
    r"everyone else|better than yesterday|don't waste)\b",
    re.IGNORECASE,
)
_NUMBER = re.compile(r"\d+")


@dataclass
class ChainGuardResult:
    accepted: bool
    insights: list[dict]
    highlight_media_ids: list[uuid.UUID]
    directive: str | None = None
    reason: str | None = None


def _valid_uuid(raw: str) -> uuid.UUID | None:
    try:
        return uuid.UUID(str(raw))
    except (ValueError, AttributeError, TypeError):
        return None


def _source_numbers(ctx: WeeklyContext) -> set[int]:
    """Numbers that appear anywhere inside the stored source recaps — a
    candidate may restate them but may not invent new quantities."""
    allowed: set[int] = {ctx.days_covered, len(ctx.daily_recaps)}
    for ref in ctx.daily_recaps:
        for text in [ref.narrative, ref.directive_for_next_cycle or ""]:
            allowed.update(int(m) for m in _NUMBER.findall(text))
        for ins in ref.insights:
            allowed.update(int(m) for m in _NUMBER.findall(str(ins.get("text", ""))))
    return allowed


def _weekly_claim_supported(ctx: WeeklyContext, text: str) -> bool:
    lowered = text.lower()
    if _SHAME.search(lowered) or _COERCE.search(lowered):
        return False
    allowed = _source_numbers(ctx)
    return all(int(n) in allowed for n in _NUMBER.findall(text))


def guard_weekly(ctx: WeeklyContext, candidate: RecapCandidate) -> ChainGuardResult:
    valid_ids = set(ctx.evidence_event_ids)
    valid_media = set(ctx.highlight_media_ids)

    insights: list[dict] = []
    for ins in candidate.insights:
        ids = [_valid_uuid(i) for i in ins.evidence_event_ids]
        ids = [i for i in ids if i is not None]
        if not ids or any(i not in valid_ids for i in ids):
            continue
        if not _weekly_claim_supported(ctx, ins.text):
            continue
        insights.append({"text": ins.text, "evidence_event_ids": [str(i) for i in ids]})

    highlights = [
        mid
        for raw in candidate.highlight_media_ids
        if (mid := _valid_uuid(raw)) is not None and mid in valid_media
    ]

    if not _weekly_claim_supported(ctx, candidate.narrative):
        return ChainGuardResult(
            accepted=False,
            insights=[],
            highlight_media_ids=[],
            reason="weekly_narrative_contains_unsupported_claims",
        )

    directive = candidate.directive_for_next_cycle
    if directive and (
        _SHAME.search(directive.lower())
        or _COERCE.search(directive.lower())
        or len(directive.strip()) > 300
    ):
        directive = None

    return ChainGuardResult(
        accepted=True,
        insights=insights,
        highlight_media_ids=highlights,
        directive=directive.strip() if directive else None,
    )


def _directive_digits_ok(ctx: DirectiveContext, content: str) -> bool:
    sources = [g.title for g in ctx.goals]
    if ctx.latest_recap is not None:
        sources.append(ctx.latest_recap.narrative)
        if ctx.latest_recap.directive_for_next_cycle:
            sources.append(ctx.latest_recap.directive_for_next_cycle)
    for num in _NUMBER.findall(content):
        if not any(num in src for src in sources):
            return False
    return True


def guard_directive(ctx: DirectiveContext, candidate: DirectiveCandidate) -> str | None:
    """Return the accepted content, or None if the candidate is unsafe."""
    content = candidate.content.strip()
    if not content or len(content) > 300:
        return None
    lowered = content.lower()
    if _SHAME.search(lowered) or _COERCE.search(lowered):
        return None
    if not _directive_digits_ok(ctx, content):
        return None
    return content


# ---------------------------------------------------------------------------
# Deterministic fallbacks — built only from stored facts.
# ---------------------------------------------------------------------------

def build_directive_fallback(ctx: DirectiveContext) -> str:
    """Prefer the stored recap's own (already guarded) next-cycle line,
    then the oldest active goal, then a light open prompt."""
    if ctx.latest_recap is not None and ctx.latest_recap.directive_for_next_cycle:
        return ctx.latest_recap.directive_for_next_cycle
    if ctx.goals:
        oldest = max(ctx.goals, key=lambda g: g.age_days)
        return f'Today, one small step on "{oldest.title}" — only if it feels right.'
    return "A fresh page — notice one small thing worth keeping today."


def build_weekly_fallback(ctx: WeeklyContext) -> dict:
    """Weekly recap assembled purely from stored daily receipts."""
    span = f"{ctx.week_start.isoformat()} – {ctx.week_end.isoformat()}"
    n = ctx.days_covered
    sentences = [f"Your week of {span}: {n} day{'s' if n != 1 else ''} with a saved receipt."]
    if ctx.missing_dates:
        sentences.append(
            f"{len(ctx.missing_dates)} day{'s' if len(ctx.missing_dates) != 1 else ''} "
            "have no receipt — unknown, and that's okay."
        )
    insights: list[dict] = []
    for ref in ctx.daily_recaps:
        if not ref.evidence_event_ids:
            continue
        summary = ref.narrative[:120] + ("…" if len(ref.narrative) > 120 else "")
        insights.append(
            {
                "text": f"{ref.period_start.isoformat()}: {summary}",
                "evidence_event_ids": [str(i) for i in ref.evidence_event_ids],
            }
        )
    directive = None
    if ctx.goals:
        oldest = max(ctx.goals, key=lambda g: g.age_days)
        directive = f'Next week, one small step on "{oldest.title}" — only if it feels right.'
    return {
        "narrative": " ".join(sentences),
        "insights": insights,
        "highlight_media_ids": [str(i) for i in ctx.highlight_media_ids[:6]],
        "directive_for_next_cycle": directive,
    }

"""Deterministic fact guard and fallback receipt (HWGA06).

Gemini proposes; code disposes. Every claim in a candidate is checked
against the DailyContext computed from the database:

- every insight must cite >= 1 id from evidence_event_ids
- highlight_media_ids must be a subset of media_asset_ids
- explicit "<number> <noun>" quantity claims must equal the computed fact
  (waters, stretches, quiet moments, minutes in a mode, active goals, ...)
- mode/duration claims may only reference modes that actually occurred
- goal-completion claims are unsupported (DailyContext carries ACTIVE
  goals only), as are dates other than the receipt's local_date
- shaming language about rest is rejected outright

A failing insight is dropped; a failing narrative rejects the whole
candidate and the workflow persists the deterministic fallback with
status=FALLBACK instead.
"""

import re
import uuid
from dataclasses import dataclass

from app.agents.schemas.receipt import RecapCandidate
from app.domain.enums import ConfirmationKind, UserMode
from app.services.daily_context import AggregatedDay

# "N <noun>" claims are compared against these computed facts. Nouns not
# listed here are not checked (the guard only rejects what it can disprove,
# and evidence ids still bind every insight to real events).
_KIND_NOUNS: dict[ConfirmationKind, tuple[str, ...]] = {
    ConfirmationKind.WATER: ("water", "hydrat"),
    ConfirmationKind.FOOD_CLEAN: ("food", "meal", "eat"),
    ConfirmationKind.STRETCH: ("stretch",),
    ConfirmationKind.POSTURE_RESET: ("posture",),
    ConfirmationKind.WALK: ("walk", "steps"),
}

_MODE_WORDS: dict[UserMode, tuple[str, ...]] = {
    UserMode.LOCKED_IN: ("locked in", "focus", "deep work"),
    UserMode.PURE_FUN_RECOVERY: ("rest", "recover", "fun", "leisure", "break"),
}

_DURATION_UNITS = ("minute", "min", "hour", "hr")
_SHAME = re.compile(
    r"\b(lazy|wasted|worthless|failed(?:\s+to)?|didn'?t bother|blew it|no excuse)\b",
    re.IGNORECASE,
)
_QUANTITY = re.compile(r"(\d+)\s*[- ]?\s*([a-zA-Z][a-zA-Z' ]{0,24})")
_DATE_LIKE = re.compile(
    r"\b(20\d\d-\d\d-\d\d|"
    r"(?:january|february|march|april|may|june|july|august|september|october|"
    r"november|december)\s+\d{1,2})\b",
    re.IGNORECASE,
)
_GOAL_DONE = re.compile(r"\b(complet\w+|finish\w+|achiev\w+|nailed|crushed)\b", re.IGNORECASE)
_GOAL_WORD = re.compile(r"\bgoal", re.IGNORECASE)
_MODE_DURATION = re.compile(
    r"\b(locked in|focus|rest|recovery|leisure|fun|break)\b[^.]*?(\d+)\s*"
    r"(minutes?|mins?|hours?|hrs?)\b",
    re.IGNORECASE,
)


@dataclass
class GuardResult:
    accepted: bool  # narrative survived
    insights: list[dict]  # cleaned, contract-shaped insight dicts
    highlight_media_ids: list[uuid.UUID]
    directive: str | None
    reason: str | None = None  # why the candidate was rejected (redacted)


def _facts(day: AggregatedDay) -> dict[str, int]:
    ctx = day.context
    facts: dict[str, int] = {}
    for kind, nouns in _KIND_NOUNS.items():
        if kind.value in ctx.confirmations:
            for n in nouns:
                facts[n] = ctx.confirmations[kind.value]
    for noun in ("quiet", "still moment", "pause"):
        facts[noun] = ctx.quiet_moments
    facts["goal"] = len(ctx.goals)
    facts["moment"] = len(ctx.media_asset_ids)
    facts["photo"] = len(ctx.media_asset_ids)
    facts["idea"] = len(ctx.ideas)
    facts["scrap"] = len(ctx.ideas)
    return facts


def _durations(day: AggregatedDay) -> dict[UserMode, int]:
    out: dict[UserMode, int] = {}
    for iv in day.context.mode_intervals:
        out[iv.mode] = out.get(iv.mode, 0) + (iv.duration_min or 0)
    return out


def _claim_supported(day: AggregatedDay, text: str) -> bool:
    """True only if every checkable assertion in `text` holds."""
    lowered = text.lower()
    if _SHAME.search(lowered):
        return False

    facts = _facts(day)
    for num_s, noun_phrase in _QUANTITY.findall(lowered):
        num = int(num_s)
        noun = noun_phrase.strip()
        for fact_noun, fact_val in facts.items():
            if noun == fact_noun or noun.startswith(fact_noun + " ") or (
                len(fact_noun) > 3 and noun.startswith(fact_noun)
            ):
                if num != fact_val:
                    return False
                break

    durations = _durations(day)
    present_modes = {iv.mode for iv in day.context.mode_intervals}
    for mode, words in _MODE_WORDS.items():
        # Duration claim against a mode: the mode must have happened and
        # the number must equal the computed duration.
        for m in _MODE_DURATION.finditer(lowered):
            if any(w in m.group(1) for w in words):
                if mode not in present_modes:
                    return False
                val = int(m.group(2))
                expected = durations.get(mode, 0)
                if m.group(3).lower().startswith(("hour", "hr")):
                    val *= 60
                if val != expected:
                    return False

    # Claiming goal completion is unsupported: DailyContext only carries
    # ACTIVE goals; nothing here can prove a goal was finished today.
    if _GOAL_WORD.search(lowered) and _GOAL_DONE.search(lowered):
        return False

    # Dates other than the receipt's own local_date are unsupported.
    for raw in _DATE_LIKE.findall(text):
        if raw and str(day.context.local_date) not in raw:
            return False
    return True


def guard(day: AggregatedDay, candidate: RecapCandidate) -> GuardResult:
    ctx = day.context
    valid_ids = set(ctx.evidence_event_ids)
    valid_media = set(ctx.media_asset_ids)

    insights: list[dict] = []
    for ins in candidate.insights:
        try:
            ids = [uuid.UUID(i) for i in ins.evidence_event_ids]
        except (ValueError, AttributeError):
            continue
        if not ids or any(i not in valid_ids for i in ids):
            continue
        if not _claim_supported(day, ins.text):
            continue
        insights.append(
            {"text": ins.text, "evidence_event_ids": [str(i) for i in ids]}
        )

    highlights: list[uuid.UUID] = []
    for raw in candidate.highlight_media_ids:
        try:
            mid = uuid.UUID(raw)
        except (ValueError, AttributeError):
            continue
        if mid in valid_media:
            highlights.append(mid)

    if not _claim_supported(day, candidate.narrative):
        return GuardResult(
            accepted=False,
            insights=[],
            highlight_media_ids=[],
            directive=None,
            reason="narrative_contains_unsupported_claims",
        )

    directive = candidate.directive_for_next_cycle
    if directive and not _claim_supported(day, directive):
        directive = None

    return GuardResult(
        accepted=True,
        insights=insights,
        highlight_media_ids=highlights,
        directive=directive.strip() or None if directive else None,
    )


# ---------------------------------------------------------------------------
# Deterministic fallback — every statement is built from DailyContext facts.
# ---------------------------------------------------------------------------

_KIND_LABELS = {
    "WATER": "glasses of water",
    "FOOD_CLEAN": "clean meals",
    "STRETCH": "stretches",
    "POSTURE_RESET": "posture resets",
    "WALK": "walks",
}
_MODE_LABELS = {
    "LOCKED_IN": "locked-in focus",
    "PURE_FUN_RECOVERY": "rest and fun",
}


def _ev(day: AggregatedDay, key: str) -> list[str]:
    return [str(i) for i in day.evidence_by_fact.get(key, [])]


def build_fallback(day: AggregatedDay) -> dict:
    """Receipt assembled purely from computed facts. Missing = unknown,
    rest is positive, nothing is shamed."""
    ctx = day.context
    sentences: list[str] = []
    insights: list[dict] = []

    logged = [
        f"{n} {_KIND_LABELS[k]}"
        for k, n in ctx.confirmations.items()
        if k in _KIND_LABELS
    ]
    if logged:
        sentences.append(f"You logged {', '.join(logged)}.")
        for kind in ctx.confirmations:
            ids = _ev(day, f"confirmation:{kind}")
            if ids:
                insights.append(
                    {
                        "text": f"{ctx.confirmations[kind]}x {kind.lower().replace('_', ' ')} confirmed.",
                        "evidence_event_ids": ids,
                    }
                )

    if ctx.quiet_moments:
        sentences.append(
            f"You marked {ctx.quiet_moments} quiet "
            f"moment{'s' if ctx.quiet_moments != 1 else ''} for yourself."
        )
        insights.append(
            {
                "text": f"{ctx.quiet_moments} quiet moment{'s' if ctx.quiet_moments != 1 else ''} recorded.",
                "evidence_event_ids": _ev(day, "quiet_moments"),
            }
        )

    for iv in ctx.mode_intervals:
        label = _MODE_LABELS.get(iv.mode.value, iv.mode.value.lower())
        if iv.duration_min:
            sentences.append(f"You spent about {iv.duration_min} minutes in {label}.")
        else:
            sentences.append(f"You were in {label}.")

    if ctx.goals:
        titles = ", ".join(f'"{g.title}"' for g in ctx.goals)
        sentences.append(f"Still in progress: {titles} — no rush, they keep.")

    if ctx.media_asset_ids:
        n = len(ctx.media_asset_ids)
        sentences.append(f"You kept {n} sensory moment{'s' if n != 1 else ''} in your vault.")
        if _ev(day, "media_captured"):
            insights.append(
                {
                    "text": f"{n} moment{'s' if n != 1 else ''} captured in the vault.",
                    "evidence_event_ids": _ev(day, "media_captured"),
                }
            )

    if ctx.ideas:
        sentences.append(
            f"And {len(ctx.ideas)} idea{'s' if len(ctx.ideas) != 1 else ''} "
            "made it into a voice scrap."
        )

    if not sentences:
        narrative = (
            f"A quiet day on {ctx.local_date.isoformat()} — nothing was logged, "
            "and that's okay. Rest and uneventful days count too."
        )
    else:
        narrative = " ".join(sentences)

    directive = None
    if ctx.goals:
        oldest = max(ctx.goals, key=lambda g: g.age_days)
        directive = (
            f"Tomorrow, one small step on \"{oldest.title}\" — only if it feels right."
        )
    elif ctx.confirmations:
        directive = "Same gentle rhythm tomorrow — tap what you do, skip what you don't."

    return {
        "narrative": narrative,
        "insights": insights,
        "highlight_media_ids": [str(i) for i in ctx.media_asset_ids[:3]],
        "directive_for_next_cycle": directive,
    }

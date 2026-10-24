"""Typed LangGraph workflow for the weekly recap (HWGA07).

    load_context -> compose_candidate -> chain_guard -> persist

- load_context: deterministic WeeklyContext built ONLY from stored DAILY
  recaps (+ active goals) — raw event history never enters the pipeline
- compose_candidate: provider adapter call; failure -> FALLBACK path
- chain_guard: deterministic validation; invalid narrative -> FALLBACK
- persist: idempotent upsert on (user_id, WEEKLY, week_start) with
  source_recap_ids recording exactly which daily recaps were consumed
"""

import logging
import uuid
from datetime import date
from typing import Callable, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agents.chain_guard import build_weekly_fallback, guard_weekly
from app.agents.providers.gemini import NarrativeProvider, ProviderError
from app.agents.schemas.receipt import RecapCandidate
from app.db.models import RecapRow, User
from app.db.repositories.recaps import RecapRepository
from app.domain.enums import GenerationStatus, RecapPeriod
from app.services.weekly_context import AggregatedWeek, WeeklyContextService

logger = logging.getLogger("hwga")

WeekBuilder = Callable[[uuid.UUID, date], AggregatedWeek]


class WeeklyState(TypedDict, total=False):
    user_id: uuid.UUID
    local_date: date
    week: AggregatedWeek
    candidate: RecapCandidate | None
    provider_error: str | None
    status: GenerationStatus
    narrative: str
    insights: list[dict]
    highlight_media_ids: list[str]
    directive_for_next_cycle: str | None
    recap: RecapRow | None


def _persist_node(state: WeeklyState, session: Session) -> WeeklyState:
    """Idempotent on (user_id, WEEKLY, week_start)."""
    ctx = state["week"].context
    repo = RecapRepository(session)
    existing = repo.get_for_period(ctx.user_id, RecapPeriod.WEEKLY, ctx.week_start)
    if existing is not None and not existing.stale:
        return {**state, "recap": existing}

    row = existing or RecapRow(
        user_id=ctx.user_id,
        period_type=RecapPeriod.WEEKLY,
        period_start=ctx.week_start,
        period_end=ctx.week_end,
    )
    row.period_end = ctx.week_end
    row.narrative = state["narrative"]
    row.insights = state["insights"]
    row.highlight_media_ids = state["highlight_media_ids"]
    row.directive_for_next_cycle = state["directive_for_next_cycle"]
    row.source_recap_ids = [str(r.id) for r in state["week"].source_rows]
    row.status = state["status"]
    row.stale = False
    try:
        repo.add(row)
        session.commit()
    except IntegrityError:
        session.rollback()
        row = repo.get_for_period(ctx.user_id, RecapPeriod.WEEKLY, ctx.week_start)
        if row is None:
            raise
    return {**state, "recap": row}


def build_weekly_graph(
    session: Session,
    provider: NarrativeProvider,
    context_builder: WeekBuilder | None = None,
):
    def load_context(state: WeeklyState) -> WeeklyState:
        builder = context_builder or (
            lambda uid, d: WeeklyContextService(session).build(session.get(User, uid), d)
        )
        return {**state, "week": builder(state["user_id"], state["local_date"])}

    def compose_candidate(state: WeeklyState) -> WeeklyState:
        try:
            candidate = provider.generate_weekly(state["week"].context)
        except ProviderError as exc:
            logger.warning("weekly provider failure kind=%s", exc.kind.value)
            return {**state, "candidate": None, "provider_error": exc.kind.value}
        return {**state, "candidate": candidate, "provider_error": None}

    def chain_guard(state: WeeklyState) -> WeeklyState:
        candidate = state.get("candidate")
        if candidate is not None:
            result = guard_weekly(state["week"].context, candidate)
            if result.accepted:
                return {
                    **state,
                    "status": GenerationStatus.GENERATED,
                    "narrative": candidate.narrative,
                    "insights": result.insights,
                    "highlight_media_ids": [str(i) for i in result.highlight_media_ids],
                    "directive_for_next_cycle": result.directive,
                }
            logger.warning("weekly guard rejected candidate: %s", result.reason)
        fallback = build_weekly_fallback(state["week"].context)
        return {
            **state,
            "status": GenerationStatus.FALLBACK,
            "narrative": fallback["narrative"],
            "insights": fallback["insights"],
            "highlight_media_ids": fallback["highlight_media_ids"],
            "directive_for_next_cycle": fallback["directive_for_next_cycle"],
        }

    def persist(state: WeeklyState) -> WeeklyState:
        try:
            return _persist_node(state, session)
        except Exception:
            session.rollback()
            logger.exception("weekly persist failed")
            return {**state, "status": GenerationStatus.FAILED, "recap": None}

    graph = StateGraph(WeeklyState)
    graph.add_node("load_context", load_context)
    graph.add_node("compose_candidate", compose_candidate)
    graph.add_node("chain_guard", chain_guard)
    graph.add_node("persist", persist)
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "compose_candidate")
    graph.add_edge("compose_candidate", "chain_guard")
    graph.add_edge("chain_guard", "persist")
    graph.add_edge("persist", END)
    return graph.compile()

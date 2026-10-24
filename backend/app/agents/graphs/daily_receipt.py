"""Typed LangGraph workflow for the nightly receipt (HWGA06).

Bounded, linear pipeline — nodes delegate, they do not compute facts or
touch the provider SDK directly:

    load_context -> compose_candidate -> fact_guard -> persist

- load_context: deterministic DailyContext aggregation (DB via service)
- compose_candidate: provider adapter call; failure -> FALLBACK path
- fact_guard: deterministic validation; invalid narrative -> FALLBACK
- persist: idempotent upsert on (user_id, period_type, period_start) via
  the recap repository; observable failures -> FAILED, never silent

langgraph 0.6.11 API: `StateGraph(TypedDict)`, `add_node`, `add_edge`,
`compile().invoke(initial_state)`.
"""

import logging
import uuid
from datetime import date
from typing import Callable, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agents.fact_guard import build_fallback, guard
from app.agents.providers.gemini import NarrativeProvider, ProviderError
from app.agents.schemas.receipt import RecapCandidate
from app.db.models import RecapRow, User
from app.db.repositories.recaps import RecapRepository
from app.domain.enums import GenerationStatus, RecapPeriod
from app.schemas.contracts import DailyContext
from app.services.daily_context import AggregatedDay, DailyContextService

logger = logging.getLogger("hwga")

ContextBuilder = Callable[[uuid.UUID, date], AggregatedDay]
Persister = Callable[["ReceiptState"], RecapRow]


class ReceiptState(TypedDict, total=False):
    user_id: uuid.UUID
    local_date: date
    day: AggregatedDay
    candidate: RecapCandidate | None
    provider_error: str | None
    status: GenerationStatus
    narrative: str
    insights: list[dict]
    highlight_media_ids: list[str]
    directive_for_next_cycle: str | None
    recap: RecapRow | None


def _persist_node(state: ReceiptState, session: Session) -> ReceiptState:
    """Idempotent on (user_id, period_type, period_start): a concurrent or
    repeated run loses the unique race and returns the stored row."""
    ctx: DailyContext = state["day"].context
    repo = RecapRepository(session)
    existing = repo.get_for_period(ctx.user_id, RecapPeriod.DAILY, ctx.local_date)
    if existing is not None and not existing.stale:
        return {**state, "recap": existing}

    row = existing or RecapRow(
        user_id=ctx.user_id,
        period_type=RecapPeriod.DAILY,
        period_start=ctx.local_date,
        period_end=ctx.local_date,
    )
    row.narrative = state["narrative"]
    row.insights = state["insights"]
    row.highlight_media_ids = state["highlight_media_ids"]
    row.directive_for_next_cycle = state["directive_for_next_cycle"]
    row.source_recap_ids = []
    row.status = state["status"]
    row.stale = False
    try:
        repo.add(row)
        session.commit()
    except IntegrityError:
        session.rollback()
        row = repo.get_for_period(ctx.user_id, RecapPeriod.DAILY, ctx.local_date)
        if row is None:
            raise
    return {**state, "recap": row}


def build_daily_graph(
    session: Session,
    provider: NarrativeProvider,
    context_builder: ContextBuilder | None = None,
):
    """Compile the daily-receipt graph for one request/job run."""

    def load_context(state: ReceiptState) -> ReceiptState:
        builder = context_builder or (
            lambda uid, d: DailyContextService(session).build(session.get(User, uid), d)
        )
        return {**state, "day": builder(state["user_id"], state["local_date"])}

    def compose_candidate(state: ReceiptState) -> ReceiptState:
        try:
            candidate = provider.generate_receipt(state["day"].context)
        except ProviderError as exc:
            logger.warning("receipt provider failure kind=%s", exc.kind.value)
            return {
                **state,
                "candidate": None,
                "provider_error": exc.kind.value,
            }
        return {**state, "candidate": candidate, "provider_error": None}

    def fact_guard(state: ReceiptState) -> ReceiptState:
        candidate = state.get("candidate")
        if candidate is not None:
            result = guard(state["day"], candidate)
            if result.accepted:
                return {
                    **state,
                    "status": GenerationStatus.GENERATED,
                    "narrative": candidate.narrative,
                    "insights": result.insights,
                    "highlight_media_ids": [str(i) for i in result.highlight_media_ids],
                    "directive_for_next_cycle": result.directive,
                }
            logger.warning("receipt fact guard rejected candidate: %s", result.reason)
        fallback = build_fallback(state["day"])
        return {
            **state,
            "status": GenerationStatus.FALLBACK,
            "narrative": fallback["narrative"],
            "insights": fallback["insights"],
            "highlight_media_ids": fallback["highlight_media_ids"],
            "directive_for_next_cycle": fallback["directive_for_next_cycle"],
        }

    def persist(state: ReceiptState) -> ReceiptState:
        try:
            return _persist_node(state, session)
        except Exception:
            session.rollback()
            logger.exception("receipt persist failed")
            return {**state, "status": GenerationStatus.FAILED, "recap": None}

    graph = StateGraph(ReceiptState)
    graph.add_node("load_context", load_context)
    graph.add_node("compose_candidate", compose_candidate)
    graph.add_node("fact_guard", fact_guard)
    graph.add_node("persist", persist)
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "compose_candidate")
    graph.add_edge("compose_candidate", "fact_guard")
    graph.add_edge("fact_guard", "persist")
    graph.add_edge("persist", END)
    return graph.compile()

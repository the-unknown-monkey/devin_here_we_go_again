"""Typed LangGraph workflow for the morning directive (HWGA07).

    load_context -> compose_candidate -> guard -> persist

- load_context: deterministic DirectiveContext built from stored DAILY
  recaps and active goals — the model may not see anything else
- compose_candidate: provider adapter call; failure -> FALLBACK path
- guard: shame/coercion/unverifiable-quantity checks -> FALLBACK
- persist: idempotent on (user_id, for_date); `shown_at` is owned by the
  service layer (display dedupe), not by generation
"""

import logging
import uuid
from datetime import date
from typing import Callable, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.agents.chain_guard import build_directive_fallback, guard_directive
from app.agents.providers.gemini import NarrativeProvider, ProviderError
from app.agents.schemas.context import DirectiveContext
from app.agents.schemas.directive import DirectiveCandidate
from app.db.models import MorningDirectiveRow, User
from app.db.repositories.recaps import DirectiveRepository
from app.domain.enums import GenerationStatus
from app.services.directives import DirectiveContextBuilder

logger = logging.getLogger("hwga")

ContextBuilder = Callable[[uuid.UUID, date], DirectiveContext]


class DirectiveState(TypedDict, total=False):
    user_id: uuid.UUID
    for_date: date
    ctx: DirectiveContext
    candidate: DirectiveCandidate | None
    provider_error: str | None
    status: GenerationStatus
    content: str
    directive: MorningDirectiveRow | None


def _persist_node(state: DirectiveState, session: Session) -> DirectiveState:
    """Idempotent on (user_id, for_date): retries and duplicate app opens
    can never create a second directive for the same day."""
    ctx = state["ctx"]
    repo = DirectiveRepository(session)
    existing = repo.get_for_date(ctx.user_id, ctx.for_date)
    if existing is not None:
        return {**state, "directive": existing}

    row = MorningDirectiveRow(
        user_id=ctx.user_id,
        for_date=ctx.for_date,
        content=state["content"],
        source_recap_id=(
            ctx.latest_recap.recap_id if ctx.latest_recap is not None else None
        ),
        status=state["status"],
    )
    try:
        repo.add(row)
        session.commit()
    except IntegrityError:
        session.rollback()
        row = repo.get_for_date(ctx.user_id, ctx.for_date)
        if row is None:
            raise
    return {**state, "directive": row}


def build_directive_graph(
    session: Session,
    provider: NarrativeProvider,
    context_builder: ContextBuilder | None = None,
):
    def load_context(state: DirectiveState) -> DirectiveState:
        builder = context_builder or (
            lambda uid, d: DirectiveContextBuilder(session).build(session.get(User, uid), d)
        )
        return {**state, "ctx": builder(state["user_id"], state["for_date"])}

    def compose_candidate(state: DirectiveState) -> DirectiveState:
        try:
            candidate = provider.generate_directive(state["ctx"])
        except ProviderError as exc:
            logger.warning("directive provider failure kind=%s", exc.kind.value)
            return {**state, "candidate": None, "provider_error": exc.kind.value}
        return {**state, "candidate": candidate, "provider_error": None}

    def guard(state: DirectiveState) -> DirectiveState:
        candidate = state.get("candidate")
        if candidate is not None:
            content = guard_directive(state["ctx"], candidate)
            if content is not None:
                return {
                    **state,
                    "status": GenerationStatus.GENERATED,
                    "content": content,
                }
            logger.warning("directive guard rejected candidate")
        return {
            **state,
            "status": GenerationStatus.FALLBACK,
            "content": build_directive_fallback(state["ctx"]),
        }

    def persist(state: DirectiveState) -> DirectiveState:
        try:
            return _persist_node(state, session)
        except Exception:
            session.rollback()
            logger.exception("directive persist failed")
            return {**state, "status": GenerationStatus.FAILED, "directive": None}

    graph = StateGraph(DirectiveState)
    graph.add_node("load_context", load_context)
    graph.add_node("compose_candidate", compose_candidate)
    graph.add_node("guard", guard)
    graph.add_node("persist", persist)
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "compose_candidate")
    graph.add_edge("compose_candidate", "guard")
    graph.add_edge("guard", "persist")
    graph.add_edge("persist", END)
    return graph.compile()

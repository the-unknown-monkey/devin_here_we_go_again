"""/goals — Rule of 3 lifecycle (contracts §3). Cap enforcement is the D14
serialized transaction inside GoalService, not this router."""

import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.security import require_auth
from app.db.models import User
from app.db.session import get_session
from app.domain.errors import DomainError
from app.schemas.contracts import GoalItem
from app.services.goals import GoalService

router = APIRouter()


class GoalCreateIn(BaseModel):
    title: str = Field(min_length=1, max_length=500)


@router.get("/goals", response_model=List[GoalItem])
def get_goals(
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
):
    return GoalService(session).list(user)


@router.post("/goals", response_model=GoalItem, status_code=201)
def post_goal(
    payload: GoalCreateIn,
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
):
    try:
        return GoalService(session).add(user, payload.title)
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.payload()) from exc


@router.post("/goals/{goal_id}/complete", response_model=GoalItem)
def complete_goal(
    goal_id: uuid.UUID,
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
):
    try:
        return GoalService(session).complete(user, goal_id)
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.payload()) from exc


@router.post("/goals/{goal_id}/retire", response_model=GoalItem)
def retire_goal(
    goal_id: uuid.UUID,
    user: User = Depends(require_auth),
    session: Session = Depends(get_session),
):
    try:
        return GoalService(session).retire(user, goal_id)
    except DomainError as exc:
        session.rollback()
        raise HTTPException(status_code=exc.status_code, detail=exc.payload()) from exc

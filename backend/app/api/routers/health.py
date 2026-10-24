"""GET /health — the only unauthenticated route (contracts §3/§4)."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}

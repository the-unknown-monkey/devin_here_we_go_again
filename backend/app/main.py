"""FastAPI app factory / entry point.

`uvicorn app.main:app --port 8000` (port locked HWGA01, D15).
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.routers import events, goals, health, me, mode
from app.core.config import get_settings
from app.core.logging import configure_logging

logger = logging.getLogger("hwga")


def _error_payload(detail: object, default_code: str) -> dict:
    if isinstance(detail, dict) and "code" in detail:
        return detail
    return {
        "code": default_code,
        "message": detail if isinstance(detail, str) else default_code,
        "details": {},
    }


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(
        settings.log_level,
        secrets=[settings.auth_token_pepper, settings.gemini_api_key],
    )

    app = FastAPI(title="hwga-backend", docs_url=None, redoc_url=None, openapi_url=None)

    @app.exception_handler(StarletteHTTPException)
    async def http_exc(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = "UNAUTHORIZED" if exc.status_code == 401 else "NOT_FOUND" if exc.status_code == 404 else "ERROR"
        return JSONResponse(
            status_code=exc.status_code,
            content=_error_payload(exc.detail, code),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exc(_: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "details": {"errors": exc.errors()},
            },
        )

    app.include_router(health.router)
    app.include_router(me.router)
    app.include_router(events.router)
    app.include_router(mode.router)
    app.include_router(goals.router)
    return app


app = create_app()

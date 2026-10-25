"""Server-side Gemini adapter (contracts.md §4 Gemini boundary).

- Credentials come from backend settings (`GEMINI_API_KEY`) only; the key
  never leaves the backend and never reaches Flutter.
- Timeout-bounded calls with at most 2 retries on transient failures
  (timeout / 5xx). Quota and client errors fail immediately — retrying a
  quota error only burns quota.
- Structured output is requested via response_mime_type +
  response_json_schema; the parsed candidate is still unvalidated input
  and must pass the deterministic fact guard before persistence.
- The adapter holds no DB session and touches no files — call services
  own all persistence.
- The model receives typed context objects only: `DailyContext` for
  receipts, `WeeklyContext` (stored daily recap objects) for the weekly
  roll-up, and `DirectiveContext` for the morning directive. Raw event
  history and media bytes are never sent.

Verified against google-genai 1.75.0: `genai.Client(api_key=...,
http_options=HttpOptions(timeout=<ms>))`,
`client.models.generate_content(model=..., contents=str,
config=GenerateContentConfig(...))` returning `.text`.
"""

import logging
from enum import Enum
from typing import Protocol, TypeVar

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ValidationError

from app.agents.prompts.daily import SYSTEM_INSTRUCTION, daily_prompt
from app.agents.prompts.directive import (
    DIRECTIVE_SYSTEM_INSTRUCTION,
    directive_prompt,
)
from app.agents.prompts.weekly import WEEKLY_SYSTEM_INSTRUCTION, weekly_prompt
from app.agents.schemas.context import DirectiveContext, WeeklyContext
from app.agents.schemas.directive import DirectiveCandidate
from app.agents.schemas.receipt import RecapCandidate
from app.schemas.contracts import DailyContext

logger = logging.getLogger("hwga")

DEFAULT_MODEL = "gemini-3.5-flash"
_TIMEOUT_MS = 20_000
_MAX_RETRIES = 2  # per contracts.md §4: at most 2 retries

_T = TypeVar("_T", bound=BaseModel)


class ProviderErrorKind(str, Enum):
    TIMEOUT = "TIMEOUT"
    QUOTA = "QUOTA"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    UNAVAILABLE = "UNAVAILABLE"
    NO_KEY = "NO_KEY"


class ProviderError(Exception):
    """Typed provider failure; the workflow maps it to FALLBACK — it is
    never swallowed and never reported as a generation success."""

    def __init__(self, kind: ProviderErrorKind, message: str):
        super().__init__(message)
        self.kind = kind
        self.message = message


class NarrativeProvider(Protocol):
    """The seam every generation LLM call goes through. Tests inject
    fakes; the workflows never see SDK types."""

    def generate_receipt(self, context: DailyContext) -> RecapCandidate: ...

    def generate_weekly(self, context: WeeklyContext) -> RecapCandidate: ...

    def generate_directive(self, context: DirectiveContext) -> DirectiveCandidate: ...


def _classify(exc: BaseException) -> ProviderErrorKind:
    if isinstance(exc, httpx.TimeoutException):
        return ProviderErrorKind.TIMEOUT
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code == 429:
        return ProviderErrorKind.QUOTA
    if isinstance(exc, genai_errors.ServerError):
        return ProviderErrorKind.UNAVAILABLE
    if isinstance(exc, genai_errors.ClientError):
        return ProviderErrorKind.UNAVAILABLE
    if isinstance(exc, genai_errors.APIError):
        return ProviderErrorKind.UNAVAILABLE
    return ProviderErrorKind.UNAVAILABLE


class GeminiProvider:
    """google-genai adapter. Typed context in, candidate JSON out.
    No media bytes are sent (VOICE STT is the only approved exception and
    is not wired in this phase — see status.md)."""

    def __init__(
        self,
        api_key: str | None,
        model: str = DEFAULT_MODEL,
        timeout_ms: int = _TIMEOUT_MS,
        max_retries: int = _MAX_RETRIES,
    ):
        self._api_key = api_key
        self._model = model
        self._timeout_ms = timeout_ms
        self._max_retries = max_retries
        self._client: genai.Client | None = None

    def _get_client(self) -> genai.Client:
        if self._client is None:
            self._client = genai.Client(
                api_key=self._api_key,
                http_options=types.HttpOptions(timeout=self._timeout_ms),
            )
        return self._client

    def _generate_once(
        self,
        prompt: str,
        system_instruction: str,
        schema: type[_T],
    ) -> _T:
        response = self._get_client().models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_json_schema=schema.model_json_schema(),
                temperature=0.3,
                max_output_tokens=8192,
            ),
        )
        text = response.text or ""
        try:
            return schema.model_validate_json(text)
        except (ValidationError, ValueError) as exc:
            raise ProviderError(
                ProviderErrorKind.INVALID_OUTPUT,
                f"Model output failed schema validation: {exc.__class__.__name__}",
            ) from exc

    def _call(
        self,
        prompt: str,
        system_instruction: str,
        schema: type[_T],
        label: str,
    ) -> _T:
        if not self._api_key:
            raise ProviderError(
                ProviderErrorKind.NO_KEY,
                "GEMINI_API_KEY not configured on the backend",
            )
        last: ProviderError | None = None
        for attempt in range(1 + self._max_retries):
            try:
                return self._generate_once(prompt, system_instruction, schema)
            except ProviderError:
                raise  # schema/parse failure — retrying won't fix the shape
            except Exception as exc:  # SDK/network failures
                kind = _classify(exc)
                last = ProviderError(kind, f"Gemini call failed ({kind.value})")
                logger.warning(
                    "gemini_%s attempt=%d kind=%s err=%s",
                    label,
                    attempt + 1,
                    kind.value,
                    exc.__class__.__name__,
                )
                if kind not in (ProviderErrorKind.TIMEOUT, ProviderErrorKind.UNAVAILABLE):
                    break  # quota/client errors are not retried
        assert last is not None
        raise last

    def generate_receipt(self, context: DailyContext) -> RecapCandidate:
        return self._call(
            daily_prompt(context), SYSTEM_INSTRUCTION, RecapCandidate, "receipt"
        )

    def generate_weekly(self, context: WeeklyContext) -> RecapCandidate:
        return self._call(
            weekly_prompt(context),
            WEEKLY_SYSTEM_INSTRUCTION,
            RecapCandidate,
            "weekly",
        )

    def generate_directive(self, context: DirectiveContext) -> DirectiveCandidate:
        return self._call(
            directive_prompt(context),
            DIRECTIVE_SYSTEM_INSTRUCTION,
            DirectiveCandidate,
            "directive",
        )

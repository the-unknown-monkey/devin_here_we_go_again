"""Structured-output contract for the Gemini directive candidate (HWGA07).

The model proposes a single line of content. Deterministic code decides
whether it is grounded and safe before anything is persisted.
"""

from pydantic import BaseModel, ConfigDict, Field


class DirectiveCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    content: str = Field(min_length=1, max_length=300)

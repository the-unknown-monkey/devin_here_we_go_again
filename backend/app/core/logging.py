"""Structured-ish safe logging: stdlib JSON lines plus a filter that redacts
secrets and bearer tokens so they can never reach log output (TRD §6.2)."""

import json
import logging
import re
from datetime import datetime, timezone

_BEARER_RE = re.compile(r"(?i)bearer\s+[A-Za-z0-9._~+/=-]+")
_REDACTED = "[REDACTED]"

# Extra secret values registered at startup (pepper, API keys) are redacted
# verbatim anywhere they appear in a record.
_secret_fragments: list[str] = []


def register_secret(value: str | None) -> None:
    if value and len(value) >= 8 and value not in _secret_fragments:
        _secret_fragments.append(value)


def _redact(text: str) -> str:
    text = _BEARER_RE.sub("Bearer " + _REDACTED, text)
    for secret in _secret_fragments:
        text = text.replace(secret, _REDACTED)
    return text


class SecretRedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact(str(record.msg))
        if record.args:
            record.args = tuple(
                _redact(str(a)) if isinstance(a, str) else a for a in record.args
            )
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            payload["exc"] = _redact(self.formatException(record.exc_info))
        return _redact(json.dumps(payload, default=str))


def configure_logging(level: str = "INFO", secrets: list[str | None] | None = None) -> None:
    for s in secrets or []:
        register_secret(s)
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(SecretRedactingFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

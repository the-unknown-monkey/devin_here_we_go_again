"""Secret-redaction checks: bearer tokens and registered secrets must never
reach log output (TRD §6.2)."""

import logging

from app.core.logging import JsonFormatter, SecretRedactingFilter, register_secret


def _record(msg: str) -> logging.LogRecord:
    rec = logging.LogRecord("t", logging.INFO, __file__, 1, msg, None, None)
    SecretRedactingFilter().filter(rec)
    return rec


def test_bearer_token_redacted():
    rec = _record("got Authorization: Bearer abcdef0123456789abcdef")
    assert "abcdef0123456789abcdef" not in rec.msg
    assert "[REDACTED]" in rec.msg


def test_registered_secret_redacted_in_json_output():
    secret = "pepper-value-0123456789-unique"
    register_secret(secret)
    rec = _record(f"config dump pepper={secret} done")
    out = JsonFormatter().format(rec)
    assert secret not in out
    assert "[REDACTED]" in out


def test_normal_message_untouched():
    rec = _record("server started on port 8000")
    assert rec.msg == "server started on port 8000"

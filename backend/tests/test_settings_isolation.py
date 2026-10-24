"""Guard: tests can never be pointed at the dev DB (TRD §6.5)."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_test_db_equal_to_dev_db_rejected():
    url = "postgresql+psycopg://hwga:hwga@127.0.0.1:55432/hwga"
    with pytest.raises(ValidationError):
        Settings(database_url=url, test_database_url=url, auth_token_pepper="x" * 16)


def test_bad_timezone_rejected():
    with pytest.raises(ValidationError):
        Settings(user_timezone="Not/AZone", auth_token_pepper="x" * 16)

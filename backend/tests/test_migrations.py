"""Migration check on the disposable test DB only (55433)."""

from sqlalchemy import inspect, text

EXPECTED_TABLES = {
    "alembic_version",
    "users",
    "auth_tokens",
    "events",
    "mode_intervals",
    "goals",
    "media_assets",
    "recaps",
    "morning_directives",
}


def test_migrations_applied_on_test_db(test_engine):
    inspector = inspect(test_engine)
    assert EXPECTED_TABLES <= set(inspector.get_table_names())
    with test_engine.connect() as conn:
        head = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    assert head is not None

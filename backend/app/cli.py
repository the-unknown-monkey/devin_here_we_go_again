"""Backend bootstrap CLI (D07).

    uv run python -m app.cli provision-token

Generates a bearer token, stores HMAC-SHA256(pepper, token) in `auth_tokens`,
and prints the plaintext token exactly once. Rotate by re-running and
re-entering the new token on the phone.
"""

import argparse
import logging
import sys

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.security import generate_token, hash_token
from app.db.repositories.users import AuthTokenRepository, UserRepository
from app.db.session import get_sessionmaker

logger = logging.getLogger("hwga.cli")


def provision_token() -> int:
    settings = get_settings()
    configure_logging(settings.log_level, secrets=[settings.auth_token_pepper])
    if not settings.auth_token_pepper:
        print("AUTH_TOKEN_PEPPER is not set; refusing to provision.", file=sys.stderr)
        return 2

    token = generate_token()
    digest = hash_token(token, settings.auth_token_pepper)

    with get_sessionmaker()() as session:
        user = UserRepository(session).get_or_create_single_user(settings.user_timezone)
        AuthTokenRepository(session).add(user.id, digest)
        session.commit()

    # Printed once to the operator's terminal; never logged.
    print(f"Bearer token (shown once — store it on the phone):\n{token}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="hwga-cli")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("provision-token", help="issue + store a hashed bearer token")
    args = parser.parse_args()
    if args.command == "provision-token":
        return provision_token()
    return 2


if __name__ == "__main__":
    sys.exit(main())

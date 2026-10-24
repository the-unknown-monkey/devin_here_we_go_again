"""Domain errors mapped to locked ErrorResponse codes (contracts.md §4).

Services raise these; routers translate them into HTTPException detail dicts
so every error body stays `{code, message, details}`.
"""


class DomainError(Exception):
    def __init__(self, code: str, message: str, status_code: int, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

    def payload(self) -> dict:
        return {"code": self.code, "message": self.message, "details": self.details}


def validation(message: str, details: dict | None = None) -> DomainError:
    return DomainError("VALIDATION_ERROR", message, 422, details)


def invalid_mode_transition(message: str, details: dict | None = None) -> DomainError:
    return DomainError("INVALID_MODE_TRANSITION", message, 422, details)


def goal_cap_reached(active: int) -> DomainError:
    return DomainError(
        "GOAL_CAP_REACHED",
        "Three active goals is the limit — complete or retire one to make room.",
        409,
        {"active_goals": active},
    )


def not_found(message: str = "Not found") -> DomainError:
    return DomainError("NOT_FOUND", message, 404)

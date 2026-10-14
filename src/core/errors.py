"""Domain errors. Services raise these; the API layer maps them to HTTP responses."""


class DomainError(Exception):
    status_code: int = 400
    code: str = "domain_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(DomainError):
    status_code = 404
    code = "not_found"


class ConflictError(DomainError):
    status_code = 409
    code = "conflict"


class BusinessRuleError(DomainError):
    status_code = 422
    code = "business_rule_violation"

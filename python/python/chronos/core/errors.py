"""Fehler mit HTTP-Status und Fehlercode nach V-1 §3."""


class ChronosError(Exception):
    status = 500
    code = "internal"

    def __init__(self, message: str = "") -> None:
        super().__init__(message)
        self.message = message or self.code


class Unauthenticated(ChronosError):
    status, code = 401, "unauthenticated"


class Forbidden(ChronosError):
    status, code = 403, "forbidden"


class NotFound(ChronosError):
    status, code = 404, "not_found"


class ValidationFailed(ChronosError):
    status, code = 422, "validation_error"


class InvalidRrule(ChronosError):
    status, code = 422, "invalid_rrule"


class Conflict(ChronosError):
    status, code = 409, "conflict"


class NotUndoable(ChronosError):
    status, code = 409, "not_undoable"


class ProviderError(ChronosError):
    status, code = 502, "provider_error"

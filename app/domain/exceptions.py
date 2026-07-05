from uuid import UUID


class DomainError(Exception):
    """Базовая доменная ошибка."""

    status_code: int = 400
    code: str = "domain_error"
    default_message: str = "Domain error"

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class EventNotFound(DomainError):
    status_code = 404
    code = "event_not_found"
    default_message = "Event not found"

    def __init__(self, event_id: UUID | None = None, message: str | None = None) -> None:
        self.event_id = event_id
        super().__init__(message)


class TicketNotFound(DomainError):
    status_code = 404
    code = "ticket_not_found"
    default_message = "Ticket not found"

    def __init__(self, ticket_id: UUID | None = None, message: str | None = None) -> None:
        self.ticket_id = ticket_id
        super().__init__(message)


class SyncLockNotAcquired(DomainError):
    status_code = 409
    code = "sync_already_running"
    default_message = "Sync is already running in another process"


class IdempotencyConflict(DomainError):
    status_code = 409
    code = "idempotency_conflict"
    default_message = "Idempotency key already used with different request parameters"
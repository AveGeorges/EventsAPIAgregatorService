from enum import Enum


class SyncStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class EventStatus(str, Enum):
    NEW = "new"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    REGISTRATION_CLOSED = "registration_closed"
    FINISHED = "finished"


class OutboxEventStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"


class OutboxEventType(str, Enum):
    TICKET_PURCHASED = "ticket_purchased"

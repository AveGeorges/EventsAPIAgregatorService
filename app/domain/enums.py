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

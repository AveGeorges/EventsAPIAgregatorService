from dataclasses import dataclass
from time import monotonic
from uuid import UUID

from app.schemas.seats import SeatsResponseSchema

DEFAULT_SEATS_CACHE_TTL_SECONDS = 30


@dataclass
class _CacheEntry:
    value: SeatsResponseSchema
    expires_at: float


class SeatsCache:
    def __init__(self, ttl_seconds: float = DEFAULT_SEATS_CACHE_TTL_SECONDS) -> None:
        self._ttl_seconds = ttl_seconds
        self._entries: dict[UUID, _CacheEntry] = {}

    def get(self, event_id: UUID) -> SeatsResponseSchema | None:
        entry = self._entries.get(event_id)
        if entry is None:
            return None
        if monotonic() >= entry.expires_at:
            del self._entries[event_id]
            return None
        return entry.value

    def set(self, event_id: UUID, value: SeatsResponseSchema) -> None:
        self._entries[event_id] = _CacheEntry(
            value=value,
            expires_at=monotonic() + self._ttl_seconds,
        )

    def invalidate(self, event_id: UUID) -> None:
        self._entries.pop(event_id, None)

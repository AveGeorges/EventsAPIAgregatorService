from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domain.exceptions import EventNotFound
from app.integrations.events_provider.client import EventsProviderClient
from app.integrations.events_provider.schemas import ProviderSeatsSchema
from app.repositories.event_repository import EventRepository
from app.schemas.seats import SeatsResponseSchema
from app.services.seats_cache import SeatsCache

_default_cache = SeatsCache(ttl_seconds=settings.SEATS_CACHE_TTL_SECONDS)


def _to_seats_response(event_id: UUID, provider_seats: ProviderSeatsSchema) -> SeatsResponseSchema:
    return SeatsResponseSchema(event_id=event_id, available_seats=provider_seats.seats)


class SeatsService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        provider_client: EventsProviderClient | None = None,
        cache: SeatsCache | None = None,
    ) -> None:
        self._session = session
        self._provider_client = provider_client
        self._cache = cache or _default_cache
        self._event_repo = EventRepository(session)

    async def get_seats(self, event_id: UUID) -> SeatsResponseSchema:
        if self._provider_client is None:
            raise RuntimeError("provider_client is required for get_seats")

        event = await self._event_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFound(event_id)

        cached = self._cache.get(event_id)
        if cached is not None:
            return cached

        provider_seats = await self._provider_client.get_seats(event_id)
        result = _to_seats_response(event_id, provider_seats)
        self._cache.set(event_id, result)
        return result

    def invalidate(self, event_id: UUID) -> None:
        self._cache.invalidate(event_id)

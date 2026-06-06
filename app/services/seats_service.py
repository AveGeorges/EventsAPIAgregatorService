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


class SeatsService:
    @staticmethod
    async def get_seats(
        session: AsyncSession,
        event_id: UUID,
        *,
        provider_client: EventsProviderClient,
        cache: SeatsCache | None = None,
    ) -> SeatsResponseSchema:
        seats_cache = cache or _default_cache

        event = await EventRepository.get_by_id(session, event_id)
        if event is None:
            raise EventNotFound(event_id)

        cached = seats_cache.get(event_id)
        if cached is not None:
            return cached

        provider_seats = await provider_client.get_seats(event_id)
        result = SeatsService._to_response(provider_seats)
        seats_cache.set(event_id, result)
        return result

    @staticmethod
    def invalidate(event_id: UUID, *, cache: SeatsCache | None = None) -> None:
        (cache or _default_cache).invalidate(event_id)

    @staticmethod
    def _to_response(provider_seats: ProviderSeatsSchema) -> SeatsResponseSchema:
        return SeatsResponseSchema.model_validate(provider_seats)

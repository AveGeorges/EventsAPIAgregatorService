from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.domain.exceptions import EventNotFound
from app.integrations.events_provider.schemas import ProviderSeatsSchema
from app.schemas.seats import SeatsResponseSchema
from app.services.seats_cache import SeatsCache
from app.services.seats_service import SeatsService

EVENT_ID = UUID("550e8400-e29b-41d4-a716-446655440000")


def sample_provider_seats() -> ProviderSeatsSchema:
    return ProviderSeatsSchema(event_id=EVENT_ID, available_seats=["A1", "A2"])


@pytest.mark.asyncio
@patch("app.services.seats_service.EventRepository.get_by_id", new_callable=AsyncMock)
async def test_get_seats_raises_not_found_when_event_missing(mock_get_by_id):
    mock_get_by_id.return_value = None
    provider_client = AsyncMock()
    session = AsyncMock()

    with pytest.raises(EventNotFound):
        await SeatsService.get_seats(
            session,
            EVENT_ID,
            provider_client=provider_client,
            cache=SeatsCache(),
        )

    provider_client.get_seats.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.seats_service.EventRepository.get_by_id", new_callable=AsyncMock)
async def test_get_seats_returns_cached_value_without_provider_call(mock_get_by_id):
    mock_get_by_id.return_value = MagicMock()
    provider_client = AsyncMock()
    session = AsyncMock()
    cache = SeatsCache()
    cached = SeatsResponseSchema(event_id=EVENT_ID, available_seats=["B1"])
    cache.set(EVENT_ID, cached)

    result = await SeatsService.get_seats(
        session,
        EVENT_ID,
        provider_client=provider_client,
        cache=cache,
    )

    assert result == cached
    provider_client.get_seats.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.seats_service.EventRepository.get_by_id", new_callable=AsyncMock)
async def test_get_seats_fetches_from_provider_and_caches(mock_get_by_id):
    mock_get_by_id.return_value = MagicMock()
    provider_client = AsyncMock()
    provider_client.get_seats.return_value = sample_provider_seats()
    session = AsyncMock()
    cache = SeatsCache()

    result = await SeatsService.get_seats(
        session,
        EVENT_ID,
        provider_client=provider_client,
        cache=cache,
    )

    assert result.event_id == EVENT_ID
    assert result.available_seats == ["A1", "A2"]
    assert cache.get(EVENT_ID) == result
    provider_client.get_seats.assert_awaited_once_with(EVENT_ID)


def test_invalidate_clears_cache_entry():
    cache = SeatsCache()
    cache.set(
        EVENT_ID,
        SeatsResponseSchema(event_id=EVENT_ID, available_seats=["A1"]),
    )

    SeatsService.invalidate(EVENT_ID, cache=cache)

    assert cache.get(EVENT_ID) is None

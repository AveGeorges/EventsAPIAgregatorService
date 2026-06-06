from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest

from app.domain.enums import EventStatus
from app.domain.exceptions import EventNotFound
from app.models.models import Event, Place
from app.services.event_service import EventService

EVENT_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
PLACE_ID = UUID("650e8400-e29b-41d4-a716-446655440001")


def sample_event() -> Event:
    place = Place(
        id=PLACE_ID,
        name="Конференц-зал",
        city="Москва",
        address="ул. Ленина, 1",
        seats_pattern="A1-10",
        created_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        changed_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
    )
    return Event(
        id=EVENT_ID,
        name="Конференция по Python",
        place=place,
        place_id=PLACE_ID,
        event_time=datetime(2026, 6, 7, 17, 0, tzinfo=timezone.utc),
        registration_deadline=datetime(2026, 6, 6, 17, 0, tzinfo=timezone.utc),
        status=EventStatus.PUBLISHED,
        number_of_visitors=5,
        created_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        changed_at=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
        status_changed_at=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
    )


def _mock_page_url(base, **kwargs):
    return f"{base}?page={kwargs['page']}"


@pytest.mark.asyncio
@patch.object(EventService, "_build_page_url", side_effect=_mock_page_url)
@patch("app.services.event_service.EventRepository.list_page", new_callable=AsyncMock)
@patch("app.services.event_service.EventRepository.count", new_callable=AsyncMock)
async def test_list_events_returns_page_with_next(mock_count, mock_list_page, _mock_build_url):
    mock_count.return_value = 50
    mock_list_page.return_value = [sample_event()]
    session = AsyncMock()

    result = await EventService.list_events(
        session,
        events_base_url="http://test/api/events",
        date_from=date(2026, 6, 6),
        page=1,
        page_size=20,
    )

    assert result.count == 50
    assert result.next == "http://test/api/events?page=2"
    assert result.previous is None
    assert len(result.results) == 1
    assert result.results[0].id == EVENT_ID
    assert result.results[0].place.city == "Москва"
    mock_count.assert_awaited_once_with(session, date_from=date(2026, 6, 6))
    mock_list_page.assert_awaited_once_with(
        session,
        date_from=date(2026, 6, 6),
        offset=0,
        limit=20,
    )


@pytest.mark.asyncio
async def test_build_page_url_includes_date_from():
    url = EventService._build_page_url(
        "http://test/api/events",
        page=2,
        page_size=100,
        date_from=date(2026, 6, 6),
    )

    assert url == "http://test/api/events?page=2&page_size=100&date_from=2026-06-06"


@pytest.mark.asyncio
@patch("app.services.event_service.EventRepository.get_by_id", new_callable=AsyncMock)
async def test_get_event_returns_detail(mock_get_by_id):
    mock_get_by_id.return_value = sample_event()
    session = AsyncMock()

    result = await EventService.get_event(session, EVENT_ID)

    assert result.id == EVENT_ID
    assert result.place.seats_pattern == "A1-10"


@pytest.mark.asyncio
@patch("app.services.event_service.EventRepository.get_by_id", new_callable=AsyncMock)
async def test_get_event_raises_not_found(mock_get_by_id):
    mock_get_by_id.return_value = None
    session = AsyncMock()

    with pytest.raises(EventNotFound):
        await EventService.get_event(session, EVENT_ID)

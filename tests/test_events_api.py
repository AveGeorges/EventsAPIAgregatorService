from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from app.domain.enums import EventStatus
from app.domain.exceptions import EventNotFound
from app.integrations.events_provider.schemas import ProviderEventSchema
from app.repositories.event_repository import EventRepository
from app.repositories.place_repository import PlaceRepository
from app.schemas.event import (
    EventDetailSchema,
    EventListItemSchema,
    EventsPageResponseSchema,
    PlaceDetailSchema,
    PlaceSummarySchema,
)
from app.services.event_service import EventService
from tests.integrations.events_provider.conftest import EVENT_ID, PLACE_ID, sample_event_payload


def sample_list_item() -> EventListItemSchema:
    return EventListItemSchema(
        id=EVENT_ID,
        name="Конференция по Python",
        place=PlaceSummarySchema(
            id=PLACE_ID,
            name="Конференц-зал",
            city="Москва",
            address="ул. Ленина, 1",
        ),
        event_time=datetime(2026, 6, 7, 17, 0, tzinfo=timezone.utc),
        registration_deadline=datetime(2026, 6, 6, 17, 0, tzinfo=timezone.utc),
        status=EventStatus.PUBLISHED,
        number_of_visitors=5,
    )


def sample_detail() -> EventDetailSchema:
    return EventDetailSchema(
        id=EVENT_ID,
        name="Конференция по Python",
        place=PlaceDetailSchema(
            id=PLACE_ID,
            name="Конференц-зал",
            city="Москва",
            address="ул. Ленина, 1",
            seats_pattern="A1-10",
        ),
        event_time=datetime(2026, 6, 7, 17, 0, tzinfo=timezone.utc),
        registration_deadline=datetime(2026, 6, 6, 17, 0, tzinfo=timezone.utc),
        status=EventStatus.PUBLISHED,
        number_of_visitors=5,
    )


@patch.object(EventService, "list_events", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_list_events_http_returns_service_response(
    mock_list_events, http_client: AsyncClient
):
    mock_list_events.return_value = EventsPageResponseSchema(
        count=2,
        next="http://test/api/events?page=2&page_size=1&date_from=2026-06-06",
        previous=None,
        results=[sample_list_item()],
    )

    response = await http_client.get(
        "/api/events",
        params={"page": 1, "page_size": 1, "date_from": "2026-06-06"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert body["next"].endswith("date_from=2026-06-06")
    assert "seats_pattern" not in body["results"][0]["place"]
    mock_list_events.assert_awaited_once()
    call_kwargs = mock_list_events.await_args.kwargs
    assert call_kwargs["events_base_url"] == "http://test/api/events"
    assert call_kwargs["page"] == 1
    assert call_kwargs["page_size"] == 1


@patch.object(EventService, "get_event", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_get_event_http_returns_detail(mock_get_event, http_client: AsyncClient):
    mock_get_event.return_value = sample_detail()

    response = await http_client.get(f"/api/events/{EVENT_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(EVENT_ID)
    assert body["place"]["seats_pattern"] == "A1-10"
    mock_get_event.assert_awaited_once()


@patch.object(EventService, "get_event", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_get_event_http_returns_404(mock_get_event, http_client: AsyncClient):
    unknown_id = uuid4()
    mock_get_event.side_effect = EventNotFound(unknown_id)

    response = await http_client.get(f"/api/events/{unknown_id}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "event_not_found"


async def seed_event(
    db_session,
    *,
    event_time: str,
    event_id: UUID | None = None,
) -> ProviderEventSchema:
    payload = sample_event_payload()
    if event_id is not None:
        payload["id"] = str(event_id)
    payload["event_time"] = event_time
    event = ProviderEventSchema.model_validate(payload)
    await PlaceRepository.upsert(db_session, event.place)
    await EventRepository.upsert(db_session, event)
    await db_session.commit()
    return event


@pytest.mark.asyncio
async def test_list_events_returns_paginated_response(client: AsyncClient, db_session):
    await seed_event(db_session, event_time="2026-06-07T17:00:00+00:00")
    await seed_event(
        db_session,
        event_time="2026-06-08T17:00:00+00:00",
        event_id=uuid4(),
    )

    response = await client.get(
        "/api/events",
        params={"page": 1, "page_size": 1, "date_from": "2026-06-06"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert len(body["results"]) == 1
    assert body["next"] == (
        "http://test/api/events?page=2&page_size=1&date_from=2026-06-06"
    )
    assert body["previous"] is None
    assert set(body["results"][0]["place"]) == {"id", "name", "city", "address"}


@pytest.mark.asyncio
async def test_list_events_filters_by_date_from(client: AsyncClient, db_session):
    await seed_event(db_session, event_time="2026-05-01T17:00:00+00:00")
    await seed_event(
        db_session,
        event_time="2026-06-07T17:00:00+00:00",
        event_id=uuid4(),
    )

    response = await client.get(
        "/api/events",
        params={"date_from": "2026-06-06"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 1
    assert body["results"][0]["event_time"].startswith("2026-06-07")


@pytest.mark.asyncio
async def test_get_event_returns_detail_with_seats_pattern(
    client: AsyncClient,
    db_session,
):
    await seed_event(db_session, event_time="2026-06-07T17:00:00+00:00")

    response = await client.get(f"/api/events/{EVENT_ID}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(EVENT_ID)
    assert body["place"]["seats_pattern"] == "A1-10"
    assert body["status"] == "published"


@pytest.mark.asyncio
async def test_get_event_returns_404_when_not_found(client: AsyncClient):
    unknown_id = uuid4()
    response = await client.get(f"/api/events/{unknown_id}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "event_not_found"

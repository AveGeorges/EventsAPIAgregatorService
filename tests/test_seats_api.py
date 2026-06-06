from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import respx
from httpx import AsyncClient, Response

from app.domain.exceptions import EventNotFound
from app.schemas.seats import SeatsResponseSchema
from app.services.seats_service import SeatsService
from tests.integrations.events_provider.conftest import BASE_URL, EVENT_ID
from tests.test_events_api import seed_event


def sample_seats_response() -> SeatsResponseSchema:
    return SeatsResponseSchema(event_id=EVENT_ID, available_seats=["A1", "A2"])


@patch.object(SeatsService, "get_seats", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_get_event_seats_http_returns_service_response(
    mock_get_seats, http_client: AsyncClient
):
    mock_get_seats.return_value = sample_seats_response()

    response = await http_client.get(f"/api/events/{EVENT_ID}/seats")

    assert response.status_code == 200
    body = response.json()
    assert body["event_id"] == str(EVENT_ID)
    assert body["available_seats"] == ["A1", "A2"]
    mock_get_seats.assert_awaited_once()


@patch.object(SeatsService, "get_seats", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_get_event_seats_http_returns_404(mock_get_seats, http_client: AsyncClient):
    unknown_id = uuid4()
    mock_get_seats.side_effect = EventNotFound(unknown_id)

    response = await http_client.get(f"/api/events/{unknown_id}/seats")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "event_not_found"


@pytest.mark.asyncio
async def test_get_event_seats_fetches_from_provider(client: AsyncClient, db_session):
    SeatsService.invalidate(EVENT_ID)
    await seed_event(db_session, event_time="2026-06-07T17:00:00+00:00")

    with respx.mock:
        route = respx.get(f"{BASE_URL}api/events/{EVENT_ID}/seats/").mock(
            return_value=Response(
                200,
                json={"event_id": str(EVENT_ID), "available_seats": ["A1", "A2"]},
            )
        )

        response = await client.get(f"/api/events/{EVENT_ID}/seats")

    assert response.status_code == 200
    assert response.json()["available_seats"] == ["A1", "A2"]
    assert route.call_count == 1


@pytest.mark.asyncio
async def test_get_event_seats_uses_cache_on_second_request(client: AsyncClient, db_session):
    SeatsService.invalidate(EVENT_ID)
    await seed_event(db_session, event_time="2026-06-07T17:00:00+00:00")

    with respx.mock:
        route = respx.get(f"{BASE_URL}api/events/{EVENT_ID}/seats/").mock(
            return_value=Response(
                200,
                json={"event_id": str(EVENT_ID), "available_seats": ["A1"]},
            )
        )

        first = await client.get(f"/api/events/{EVENT_ID}/seats")
        second = await client.get(f"/api/events/{EVENT_ID}/seats")

    assert first.status_code == 200
    assert second.status_code == 200
    assert route.call_count == 1

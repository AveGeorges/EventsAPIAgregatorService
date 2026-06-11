from datetime import date
from uuid import UUID

import httpx
import pytest
import respx

from app.core.url_utils import append_query, join_url
from app.integrations.events_provider.client import EventsProviderClient
from app.integrations.events_provider.exceptions import (
    EventsProviderAuthError,
    EventsProviderNotFoundError,
)
from app.integrations.events_provider.schemas import ProviderRegisterRequestSchema
from tests.integrations.events_provider.conftest import (
    BASE_URL,
    EVENT_ID,
    PLACE_ID,
    TICKET_ID,
    provider_url,
    sample_event_payload,
    sample_events_page_payload,
)


@respx.mock
async def test_list_events_sends_api_key_and_parses_response(provider_client: EventsProviderClient):
    route = respx.get(provider_url("api", "events")).mock(
        return_value=httpx.Response(200, json=sample_events_page_payload())
    )

    page = await provider_client.list_events(date(2000, 1, 1))

    assert route.called
    request = route.calls[0].request
    assert request.headers["x-api-key"] == "test-key"
    assert request.url.params["changed_at"] == "2000-01-01"
    assert len(page.results) == 1
    assert page.results[0].id == EVENT_ID
    assert page.results[0].place.city == "Москва"


@respx.mock
async def test_iter_all_events_follows_next_url(provider_client: EventsProviderClient):
    second_event = sample_event_payload()
    second_event["id"] = "660e8400-e29b-41d4-a716-446655440099"
    second_event["name"] = "Second event"

    next_url = append_query(
        join_url(BASE_URL, "api", "events", trailing_slash=True),
        {"changed_at": "2000-01-01", "cursor": "abc"},
    )
    respx.route(method="GET", url__regex=r"http://provider\.test/api/events/.*").mock(
        side_effect=[
            httpx.Response(200, json=sample_events_page_payload(next_url=next_url)),
            httpx.Response(
                200,
                json={"next": None, "previous": next_url, "results": [second_event]},
            ),
        ]
    )

    events = [event async for event in provider_client.iter_all_events(date(2000, 1, 1))]

    assert len(events) == 2
    assert events[0].id == EVENT_ID
    assert events[1].name == "Second event"


@respx.mock
async def test_get_event(provider_client: EventsProviderClient):
    respx.get(provider_url("api", "events", EVENT_ID)).mock(
        return_value=httpx.Response(200, json=sample_event_payload())
    )

    event = await provider_client.get_event(EVENT_ID)

    assert event.id == EVENT_ID
    assert event.status.value == "published"
    assert event.place.id == PLACE_ID


@respx.mock
async def test_get_seats(provider_client: EventsProviderClient):
    respx.get(provider_url("api", "events", EVENT_ID, "seats")).mock(
        return_value=httpx.Response(
            200,
            json={"seats": ["A1", "A2"]},
        )
    )

    seats = await provider_client.get_seats(EVENT_ID)

    assert seats.seats == ["A1", "A2"]


@respx.mock
async def test_register(provider_client: EventsProviderClient):
    route = respx.post(provider_url("api", "events", EVENT_ID, "register")).mock(
        return_value=httpx.Response(201, json={"ticket_id": str(TICKET_ID)})
    )
    payload = ProviderRegisterRequestSchema(
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A15",
    )

    response = await provider_client.register(EVENT_ID, payload)

    assert response.ticket_id == TICKET_ID
    assert route.calls[0].request.content is not None
    body = route.calls[0].request.read().decode()
    assert "ivan@example.com" in body
    assert "A15" in body


@respx.mock
async def test_unregister(provider_client: EventsProviderClient):
    route = respx.delete(provider_url("api", "events", EVENT_ID, "unregister")).mock(
        return_value=httpx.Response(200, json={"success": True})
    )

    response = await provider_client.unregister(EVENT_ID, TICKET_ID)

    assert response.success is True
    body = route.calls[0].request.read().decode()
    assert str(TICKET_ID) in body
    assert "ticket_id" in body


@respx.mock
async def test_list_events_raises_auth_error(provider_client: EventsProviderClient):
    respx.get(provider_url("api", "events")).mock(
        return_value=httpx.Response(401, json={"detail": "Invalid API key"})
    )

    with pytest.raises(EventsProviderAuthError):
        await provider_client.list_events(date(2000, 1, 1))


@respx.mock
async def test_get_event_raises_not_found(provider_client: EventsProviderClient):
    missing_id = UUID("00000000-0000-0000-0000-000000000099")
    respx.get(provider_url("api", "events", missing_id)).mock(
        return_value=httpx.Response(404, json={"detail": "Event not found"})
    )

    with pytest.raises(EventsProviderNotFoundError):
        await provider_client.get_event(missing_id)

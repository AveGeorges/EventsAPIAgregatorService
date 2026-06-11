from datetime import date
from unittest.mock import AsyncMock

import httpx
import pytest
import respx

from app.core.url_utils import append_query, join_url
from app.integrations.events_provider.client import EventsProviderClient
from app.integrations.events_provider.paginator import EventsPaginator
from app.integrations.events_provider.schemas import ProviderEventSchema, ProviderEventsPageSchema
from tests.integrations.events_provider.conftest import (
    BASE_URL,
    EVENT_ID,
    sample_event_payload,
    sample_events_page_payload,
)


@respx.mock
async def test_events_paginator_follows_next_url(provider_client: EventsProviderClient):
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

    paginator = EventsPaginator(provider_client, date(2000, 1, 1))
    events = [event async for event in paginator]

    assert len(events) == 2
    assert events[0].id == EVENT_ID
    assert events[1].name == "Second event"


@pytest.mark.asyncio
async def test_events_paginator_exposes_async_iterator_protocol():
    paginator = EventsPaginator(object(), date(2000, 1, 1))

    assert paginator.__aiter__() is paginator


@pytest.mark.asyncio
async def test_events_paginator_stops_when_next_is_null_on_single_page():
    event = ProviderEventSchema.model_validate(sample_event_payload())
    mock_client = AsyncMock()
    mock_client.list_events = AsyncMock(
        return_value=ProviderEventsPageSchema(next=None, previous=None, results=[event]),
    )

    paginator = EventsPaginator(mock_client, date(2000, 1, 1))
    events = [item async for item in paginator]

    assert events == [event]
    mock_client.list_events.assert_awaited_once_with(date(2000, 1, 1))


@pytest.mark.asyncio
async def test_events_paginator_returns_empty_when_response_has_no_results():
    mock_client = AsyncMock()
    mock_client.list_events = AsyncMock(
        return_value=ProviderEventsPageSchema(next=None, previous=None, results=[]),
    )

    paginator = EventsPaginator(mock_client, date(2000, 1, 1))
    events = [item async for item in paginator]

    assert events == []
    mock_client.list_events.assert_awaited_once_with(date(2000, 1, 1))


@pytest.mark.asyncio
async def test_events_paginator_iterates_all_pages_until_next_is_null():
    first_event = ProviderEventSchema.model_validate(sample_event_payload())
    second_payload = sample_event_payload()
    second_payload["id"] = "660e8400-e29b-41d4-a716-446655440099"
    second_event = ProviderEventSchema.model_validate(second_payload)
    next_url = "http://provider.test/api/events/?cursor=abc"

    mock_client = AsyncMock()
    mock_client.list_events = AsyncMock(
        side_effect=[
            ProviderEventsPageSchema(next=next_url, previous=None, results=[first_event]),
            ProviderEventsPageSchema(next=None, previous=next_url, results=[second_event]),
        ],
    )

    paginator = EventsPaginator(mock_client, date(2000, 1, 1))
    events = [item async for item in paginator]

    assert events == [first_event, second_event]
    assert mock_client.list_events.await_count == 2
    mock_client.list_events.assert_any_await(date(2000, 1, 1))
    mock_client.list_events.assert_any_await(date(2000, 1, 1), page_url=next_url)

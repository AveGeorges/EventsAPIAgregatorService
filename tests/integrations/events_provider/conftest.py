from uuid import UUID

import httpx
import pytest

from app.integrations.events_provider.client import EventsProviderClient

EVENT_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
PLACE_ID = UUID("650e8400-e29b-41d4-a716-446655440001")
TICKET_ID = UUID("750e8400-e29b-41d4-a716-446655440002")
BASE_URL = "http://provider.test/"


def sample_place_payload() -> dict:
    return {
        "id": str(PLACE_ID),
        "name": "Конференц-зал",
        "city": "Москва",
        "address": "ул. Ленина, 1",
        "seats_pattern": "A1-10",
        "created_at": "2026-01-01T10:00:00+00:00",
        "changed_at": "2026-01-01T10:00:00+00:00",
    }


def sample_event_payload() -> dict:
    return {
        "id": str(EVENT_ID),
        "name": "Конференция по Python",
        "place": sample_place_payload(),
        "event_time": "2026-06-01T17:00:00+00:00",
        "registration_deadline": "2026-05-31T17:00:00+00:00",
        "status": "published",
        "number_of_visitors": 5,
        "created_at": "2026-01-01T10:00:00+00:00",
        "changed_at": "2026-01-02T10:00:00+00:00",
        "status_changed_at": "2026-01-02T10:00:00+00:00",
    }


def sample_events_page_payload(*, next_url: str | None = None) -> dict:
    return {
        "next": next_url,
        "previous": None,
        "results": [sample_event_payload()],
    }


@pytest.fixture
async def provider_client() -> EventsProviderClient:
    async with httpx.AsyncClient(
        base_url=BASE_URL,
        headers={"x-api-key": "test-key"},
    ) as http:
        yield EventsProviderClient(
            base_url=BASE_URL,
            api_key="test-key",
            client=http,
        )

import re
from uuid import UUID

import pytest
from httpx import AsyncClient

from app.core.metrics import HTTP_REQUESTS_TOTAL
from app.repositories.ticket_repository import TicketRepository
from tests.test_events_api import seed_event

REQUIRED_METRICS = (
    "http_requests_total",
    "http_request_duration_seconds",
    "events_provider_requests_total",
    "events_provider_request_duration_seconds",
    "tickets_created_total",
    "tickets_cancelled_total",
    "events_total",
    "cache_hits_total",
    "cache_misses_total",
)

EVENT_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TICKET_ID = UUID("750e8400-e29b-41d4-a716-446655440002")


def _counter_value(**labels: str) -> float:
    return HTTP_REQUESTS_TOTAL.labels(**labels)._value.get()


def _gauge_value(metrics_text: str, name: str) -> float:
    pattern = rf"^{re.escape(name)} (\S+)"
    for line in metrics_text.splitlines():
        if line.startswith("#"):
            continue
        match = re.match(pattern, line)
        if match:
            return float(match.group(1))
    raise AssertionError(f"Gauge {name!r} not found in metrics output")


@pytest.mark.asyncio
async def test_metrics_returns_prometheus_format(client: AsyncClient):
    response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "version=0.0.4" in response.headers["content-type"]

    body = response.text
    for metric_name in REQUIRED_METRICS:
        assert metric_name in body


@pytest.mark.asyncio
async def test_metrics_does_not_require_auth(client: AsyncClient):
    response = await client.get("/metrics")

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_metrics_endpoint_excluded_from_http_request_metrics(client: AsyncClient):
    await client.get("/metrics")
    await client.get("/metrics")

    response = await client.get("/metrics")
    assert 'endpoint="/metrics"' not in response.text


@pytest.mark.asyncio
async def test_http_middleware_records_successful_request(http_client: AsyncClient):
    before = _counter_value(method="GET", endpoint="/api/health", status="200")

    response = await http_client.get("/api/health")
    assert response.status_code == 200

    after = _counter_value(method="GET", endpoint="/api/health", status="200")
    assert after == before + 1


@pytest.mark.asyncio
async def test_metrics_reflects_database_gauges(client: AsyncClient, db_session):
    await seed_event(db_session, event_time="2026-06-07T17:00:00+00:00")
    await TicketRepository(db_session).upsert(
        ticket_id=TICKET_ID,
        event_id=EVENT_ID,
        seat="A1",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
    )
    await db_session.commit()

    response = await client.get("/metrics")
    assert response.status_code == 200

    assert _gauge_value(response.text, "events_total") == 1.0
    assert _gauge_value(response.text, "tickets_created_total") == 1.0
    assert _gauge_value(response.text, "tickets_cancelled_total") == 0.0

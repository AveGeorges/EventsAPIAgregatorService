from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.db.session import get_db
from app.domain.exceptions import SyncLockNotAcquired
from app.main import app
from app.services.event_sync_service import SyncResult


@pytest.fixture
async def sync_client(http_client: AsyncClient):
    mock_session = AsyncMock()

    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db
    yield http_client
    app.dependency_overrides.clear()


@patch("app.api.v1.sync.run_sync_with_lock", new_callable=AsyncMock)
@patch("app.api.v1.sync.create_events_provider_client")
@pytest.mark.asyncio
async def test_sync_trigger_returns_sync_result(
    mock_create_client,
    mock_run_sync_with_lock,
    sync_client: AsyncClient,
):
    provider_client = AsyncMock()
    mock_create_client.return_value = provider_client
    mock_run_sync_with_lock.return_value = SyncResult(
        events_synced=1,
        changed_at=date(2000, 1, 1),
        last_changed_at=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
    )

    response = await sync_client.post("/api/sync/trigger")

    assert response.status_code == 200
    body = response.json()
    assert body["events_synced"] == 1
    assert body["changed_at"] == "2000-01-01"
    assert body["last_changed_at"].startswith("2026-01-02T10:00:00")
    provider_client.aclose.assert_awaited_once()


@patch("app.api.v1.sync.run_sync_with_lock", new_callable=AsyncMock)
@patch("app.api.v1.sync.create_events_provider_client")
@pytest.mark.asyncio
async def test_sync_trigger_returns_409_when_sync_already_running(
    mock_create_client,
    mock_run_sync_with_lock,
    sync_client: AsyncClient,
):
    provider_client = AsyncMock()
    mock_create_client.return_value = provider_client
    mock_run_sync_with_lock.side_effect = SyncLockNotAcquired()

    response = await sync_client.post("/api/sync/trigger")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "sync_already_running"
    provider_client.aclose.assert_awaited_once()


@patch("app.api.v1.sync.run_sync_with_lock", new_callable=AsyncMock)
@patch("app.api.v1.sync.create_events_provider_client")
@pytest.mark.asyncio
async def test_sync_trigger_returns_502_on_provider_error(
    mock_create_client,
    mock_run_sync_with_lock,
    sync_client: AsyncClient,
):
    from app.integrations.events_provider.exceptions import EventsProviderServerError

    provider_client = AsyncMock()
    mock_create_client.return_value = provider_client
    mock_run_sync_with_lock.side_effect = EventsProviderServerError("HTTP 503", status_code=503)

    response = await sync_client.post("/api/sync/trigger")

    assert response.status_code == 502
    assert response.json() == {"detail": "HTTP 503"}
    provider_client.aclose.assert_awaited_once()

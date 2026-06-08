from unittest.mock import AsyncMock, patch

import pytest

from app.domain.exceptions import SyncLockNotAcquired
from app.services.sync_scheduler import run_scheduled_sync


@pytest.mark.asyncio
@patch("app.services.sync_scheduler.run_sync_with_lock", new_callable=AsyncMock)
@patch("app.services.sync_scheduler.create_events_provider_client")
@patch("app.services.sync_scheduler.AsyncSessionLocal")
async def test_run_scheduled_sync_runs_when_lock_acquired(
    mock_session_local,
    mock_create_client,
    mock_run_sync_with_lock,
):
    session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = session
    provider_client = AsyncMock()
    mock_create_client.return_value = provider_client
    mock_run_sync_with_lock.return_value = AsyncMock(events_synced=3)

    await run_scheduled_sync()

    mock_run_sync_with_lock.assert_awaited_once_with(session, provider_client)
    provider_client.aclose.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.sync_scheduler.run_sync_with_lock", new_callable=AsyncMock)
@patch("app.services.sync_scheduler.create_events_provider_client")
@patch("app.services.sync_scheduler.AsyncSessionLocal")
async def test_run_scheduled_sync_skips_when_lock_not_acquired(
    mock_session_local,
    mock_create_client,
    mock_run_sync_with_lock,
):
    session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = session
    provider_client = AsyncMock()
    mock_create_client.return_value = provider_client
    mock_run_sync_with_lock.side_effect = SyncLockNotAcquired()

    await run_scheduled_sync()

    mock_run_sync_with_lock.assert_awaited_once_with(session, provider_client)
    provider_client.aclose.assert_awaited_once()

from datetime import date, datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.exceptions import SyncLockNotAcquired
from app.services.event_sync_service import SyncResult
from app.services.sync_runner import run_sync_with_lock


def sample_sync_result() -> SyncResult:
    return SyncResult(
        events_synced=2,
        changed_at=date(2000, 1, 1),
        last_changed_at=datetime(2026, 1, 2, 10, 0, tzinfo=timezone.utc),
    )


@pytest.mark.asyncio
@patch("app.services.sync_runner.EventSyncService")
@patch("app.services.sync_runner.release_sync_lock", new_callable=AsyncMock)
@patch("app.services.sync_runner.try_acquire_sync_lock", new_callable=AsyncMock)
async def test_run_sync_with_lock_runs_sync_when_lock_acquired(
    mock_try_acquire,
    mock_release_lock,
    mock_sync_service_cls,
):
    mock_try_acquire.return_value = True
    session = AsyncMock()
    provider_client = AsyncMock()
    service = MagicMock()
    service.run_sync = AsyncMock(return_value=sample_sync_result())
    mock_sync_service_cls.return_value = service

    result = await run_sync_with_lock(session, provider_client)

    assert result.events_synced == 2
    mock_try_acquire.assert_awaited_once_with(session)
    service.run_sync.assert_awaited_once()
    mock_release_lock.assert_awaited_once_with(session)


@pytest.mark.asyncio
@patch("app.services.sync_runner.EventSyncService")
@patch("app.services.sync_runner.release_sync_lock", new_callable=AsyncMock)
@patch("app.services.sync_runner.try_acquire_sync_lock", new_callable=AsyncMock)
async def test_run_sync_with_lock_raises_when_lock_not_acquired(
    mock_try_acquire,
    mock_release_lock,
    mock_sync_service_cls,
):
    mock_try_acquire.return_value = False
    session = AsyncMock()
    provider_client = AsyncMock()

    with pytest.raises(SyncLockNotAcquired):
        await run_sync_with_lock(session, provider_client)

    mock_sync_service_cls.assert_not_called()
    mock_release_lock.assert_not_awaited()

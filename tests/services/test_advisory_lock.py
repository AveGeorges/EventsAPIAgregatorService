from unittest.mock import AsyncMock, MagicMock

import pytest

from app.db.advisory_lock import (
    SYNC_ADVISORY_LOCK_ID,
    release_sync_lock,
    try_acquire_sync_lock,
)


@pytest.mark.asyncio
async def test_try_acquire_sync_lock_returns_true():
    session = AsyncMock()
    result = MagicMock()
    result.scalar.return_value = True
    session.execute.return_value = result

    acquired = await try_acquire_sync_lock(session)

    assert acquired is True
    session.execute.assert_awaited_once()
    args, _ = session.execute.await_args
    assert args[1]["lock_id"] == SYNC_ADVISORY_LOCK_ID


@pytest.mark.asyncio
async def test_try_acquire_sync_lock_returns_false():
    session = AsyncMock()
    result = MagicMock()
    result.scalar.return_value = False
    session.execute.return_value = result

    acquired = await try_acquire_sync_lock(session)

    assert acquired is False


@pytest.mark.asyncio
async def test_release_sync_lock():
    session = AsyncMock()

    await release_sync_lock(session)

    session.execute.assert_awaited_once()
    args, _ = session.execute.await_args
    assert args[1]["lock_id"] == SYNC_ADVISORY_LOCK_ID

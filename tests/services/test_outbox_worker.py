import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest

from app.integrations.capashino.exceptions import CapashinoConflictError, CapashinoServerError
from app.services.outbox_worker import process_outbox_events, run_outbox_worker_loop

OUTBOX_ID = UUID("750e8400-e29b-41d4-a716-446655440002")


def make_pending_row() -> MagicMock:
    row = MagicMock()
    row.id = OUTBOX_ID
    row.payload = {
        "ticket_id": str(OUTBOX_ID),
        "message": "Вы успешно зарегистрированы",
        "notification_idempotency_key": "ticket-key-1",
    }
    return row


@pytest.mark.asyncio
async def test_process_outbox_events_marks_sent_on_success():
    session = AsyncMock()
    outbox_repo = MagicMock()
    outbox_repo.list_pending = AsyncMock(return_value=[make_pending_row()])
    outbox_repo.mark_sent = AsyncMock()
    capashino_client = AsyncMock()

    await process_outbox_events(outbox_repo, capashino_client, session)

    capashino_client.create_notification.assert_awaited_once()
    outbox_repo.mark_sent.assert_awaited_once_with(outbox_id=OUTBOX_ID)
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_outbox_events_marks_sent_on_conflict():
    session = AsyncMock()
    outbox_repo = MagicMock()
    outbox_repo.list_pending = AsyncMock(return_value=[make_pending_row()])
    outbox_repo.mark_sent = AsyncMock()
    capashino_client = AsyncMock()
    capashino_client.create_notification.side_effect = CapashinoConflictError("already exists")

    await process_outbox_events(outbox_repo, capashino_client, session)

    outbox_repo.mark_sent.assert_awaited_once_with(outbox_id=OUTBOX_ID)
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()


@pytest.mark.asyncio
async def test_process_outbox_events_rolls_back_on_server_error():
    session = AsyncMock()
    outbox_repo = MagicMock()
    outbox_repo.list_pending = AsyncMock(return_value=[make_pending_row()])
    outbox_repo.mark_sent = AsyncMock()
    capashino_client = AsyncMock()
    capashino_client.create_notification.side_effect = CapashinoServerError("server error")

    await process_outbox_events(outbox_repo, capashino_client, session)

    outbox_repo.mark_sent.assert_not_awaited()
    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.outbox_worker.asyncio.sleep", new_callable=AsyncMock)
@patch("app.services.outbox_worker.process_outbox_events", new_callable=AsyncMock)
@patch("app.services.outbox_worker.create_capashino_client")
@patch("app.services.outbox_worker.AsyncSessionLocal")
async def test_run_outbox_worker_loop_processes_once_then_sleeps(
    mock_session_local,
    mock_create_client,
    mock_process_outbox_events,
    mock_sleep,
):
    session = AsyncMock()
    mock_session_local.return_value.__aenter__.return_value = session
    client = AsyncMock()
    mock_create_client.return_value = client
    mock_sleep.side_effect = asyncio.CancelledError()

    with pytest.raises(asyncio.CancelledError):
        await run_outbox_worker_loop()

    mock_process_outbox_events.assert_awaited_once()
    client.aclose.assert_awaited_once()
    mock_sleep.assert_awaited_once()

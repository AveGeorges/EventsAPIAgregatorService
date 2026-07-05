from unittest.mock import AsyncMock, MagicMock, patch

import asyncio
import pytest

from app.main import lifespan


@pytest.mark.asyncio
@patch("app.main.asyncio.create_task")
@patch("app.main.AsyncIOScheduler")
@patch("app.main.settings")
async def test_lifespan_starts_scheduler_when_cron_enabled(mock_settings, mock_scheduler_cls, mock_create_task):
    mock_settings.SYNC_CRON_ENABLED = True
    mock_settings.OUTBOX_WORKER_ENABLED = False
    mock_settings.SYNC_CRON_HOUR = 3
    mock_settings.SYNC_CRON_MINUTE = 0
    mock_settings.SYNC_CRON_TIMEZONE = "UTC"

    scheduler = MagicMock()
    mock_scheduler_cls.return_value = scheduler
    app = MagicMock()

    async with lifespan(app):
        mock_scheduler_cls.assert_called_once_with(timezone="UTC")
        scheduler.add_job.assert_called_once()
        scheduler.start.assert_called_once()

    scheduler.shutdown.assert_called_once_with(wait=False)


@pytest.mark.asyncio
@patch("app.main.AsyncIOScheduler")
@patch("app.main.settings")
async def test_lifespan_starts_outbox_worker_when_enabled(mock_settings, mock_scheduler_cls):
    mock_settings.SYNC_CRON_ENABLED = False
    mock_settings.OUTBOX_WORKER_ENABLED = True
    app = MagicMock()

    async def fake_worker():
        try:
            await asyncio.Event().wait()
        except asyncio.CancelledError:
            pass

    with patch("app.main.run_outbox_worker_loop", new=fake_worker):
        with patch("app.main.asyncio.create_task", wraps=asyncio.create_task) as mock_create_task:
            async with lifespan(app):
                mock_create_task.assert_called_once()

    mock_scheduler_cls.assert_not_called()


@pytest.mark.asyncio
@patch("app.main.asyncio.create_task")
@patch("app.main.AsyncIOScheduler")
@patch("app.main.settings")
async def test_lifespan_skips_scheduler_when_cron_disabled(mock_settings, mock_scheduler_cls, mock_create_task):
    mock_settings.SYNC_CRON_ENABLED = False
    mock_settings.OUTBOX_WORKER_ENABLED = False
    app = MagicMock()

    async with lifespan(app):
        mock_scheduler_cls.assert_not_called()

from unittest.mock import MagicMock, patch

import pytest

from app.main import lifespan


@pytest.mark.asyncio
@patch("app.main.AsyncIOScheduler")
@patch("app.main.settings")
async def test_lifespan_starts_scheduler_when_cron_enabled(mock_settings, mock_scheduler_cls):
    mock_settings.SYNC_CRON_ENABLED = True
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
async def test_lifespan_skips_scheduler_when_cron_disabled(mock_settings, mock_scheduler_cls):
    mock_settings.SYNC_CRON_ENABLED = False
    app = MagicMock()

    async with lifespan(app):
        mock_scheduler_cls.assert_not_called()

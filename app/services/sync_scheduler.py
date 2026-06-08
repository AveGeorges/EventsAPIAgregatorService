import logging

from app.db.session import AsyncSessionLocal
from app.domain.exceptions import SyncLockNotAcquired
from app.integrations.events_provider.client import create_events_provider_client
from app.services.sync_runner import run_sync_with_lock

logger = logging.getLogger(__name__)


async def run_scheduled_sync() -> None:
    """Фоновая задача cron: sync с advisory lock (один winner на кластер)."""
    async with AsyncSessionLocal() as session:
        provider_client = create_events_provider_client()
        try:
            try:
                result = await run_sync_with_lock(session, provider_client)
                logger.info(
                    "Scheduled sync completed",
                    extra={"events_synced": result.events_synced},
                )
            except SyncLockNotAcquired:
                logger.info("Scheduled sync skipped: another process holds the sync lock")
            except Exception:
                logger.exception("Scheduled sync failed")
        finally:
            await provider_client.aclose()

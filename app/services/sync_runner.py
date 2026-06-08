from sqlalchemy.ext.asyncio import AsyncSession

from app.db.advisory_lock import release_sync_lock, try_acquire_sync_lock
from app.domain.exceptions import SyncLockNotAcquired
from app.integrations.events_provider.client import EventsProviderClient
from app.services.event_sync_service import EventSyncService, SyncResult


async def run_sync_with_lock(
    session: AsyncSession,
    provider_client: EventsProviderClient,
) -> SyncResult:
    """Sync с advisory lock: один активный прогон на кластер."""
    if not await try_acquire_sync_lock(session):
        raise SyncLockNotAcquired()

    try:
        return await EventSyncService(session, provider_client).run_sync()
    finally:
        await release_sync_lock(session)

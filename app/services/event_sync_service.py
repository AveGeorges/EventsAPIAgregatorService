import logging
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.events_provider.client import EventsProviderClient
from app.models.models import SyncState
from app.repositories.event_repository import EventRepository
from app.repositories.place_repository import PlaceRepository
from app.repositories.sync_state_repository import SyncStateRepository

logger = logging.getLogger(__name__)

INITIAL_CHANGED_AT = date(2000, 1, 1)


@dataclass(frozen=True)
class SyncResult:
    events_synced: int
    changed_at: date
    last_changed_at: datetime | None


def _resolve_changed_at(sync_state: SyncState) -> date:
    if sync_state.last_changed_at is None:
        return INITIAL_CHANGED_AT
    return sync_state.last_changed_at.date()


class EventSyncService:
    def __init__(self, session: AsyncSession, provider_client: EventsProviderClient) -> None:
        self._session = session
        self._provider_client = provider_client
        self._sync_state_repo = SyncStateRepository(session)
        self._place_repo = PlaceRepository(session)
        self._event_repo = EventRepository(session)

    async def run_sync(self) -> SyncResult:
        sync_state = await self._sync_state_repo.get_or_create()
        changed_at = _resolve_changed_at(sync_state)

        try:
            await self._sync_state_repo.mark_running(sync_state)
            logger.info("Event sync started", extra={"changed_at": changed_at.isoformat()})

            events_synced = 0
            max_changed_at: datetime | None = None

            async for provider_event in self._provider_client.iter_all_events(changed_at):
                await self._place_repo.upsert(provider_event.place)
                await self._event_repo.upsert(provider_event)
                if max_changed_at is None or provider_event.changed_at > max_changed_at:
                    max_changed_at = provider_event.changed_at
                events_synced += 1

            await self._sync_state_repo.mark_success(
                sync_state,
                last_changed_at=max_changed_at,
            )
            await self._session.commit()

            logger.info(
                "Event sync finished",
                extra={
                    "events_synced": events_synced,
                    "last_changed_at": max_changed_at.isoformat() if max_changed_at else None,
                },
            )
            return SyncResult(
                events_synced=events_synced,
                changed_at=changed_at,
                last_changed_at=max_changed_at,
            )
        except Exception as exc:
            await self._session.rollback()
            logger.exception("Event sync failed")
            sync_state = await self._sync_state_repo.get_or_create()
            await self._sync_state_repo.mark_failed(sync_state, str(exc))
            await self._session.commit()
            raise

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import SyncStatus
from app.models.models import SyncState, _utcnow

SYNC_STATE_ID = 1


class SyncStateRepository:
    @staticmethod
    async def get_or_create(session: AsyncSession) -> SyncState:
        result = await session.execute(select(SyncState).where(SyncState.id == SYNC_STATE_ID))
        sync_state = result.scalar_one_or_none()
        if sync_state is None:
            sync_state = SyncState(id=SYNC_STATE_ID, sync_status=SyncStatus.IDLE)
            session.add(sync_state)
            await session.flush()
        return sync_state

    @staticmethod
    async def mark_running(session: AsyncSession, sync_state: SyncState) -> None:
        sync_state.sync_status = SyncStatus.RUNNING
        sync_state.started_at = _utcnow()
        sync_state.error_message = None

    @staticmethod
    async def mark_success(
        session: AsyncSession,
        sync_state: SyncState,
        *,
        last_changed_at: datetime | None,
    ) -> None:
        sync_state.sync_status = SyncStatus.SUCCESS
        sync_state.last_sync_time = _utcnow()
        if last_changed_at is not None:
            sync_state.last_changed_at = last_changed_at
        sync_state.error_message = None

    @staticmethod
    async def mark_failed(
        session: AsyncSession,
        sync_state: SyncState,
        error_message: str,
    ) -> None:
        sync_state.sync_status = SyncStatus.FAILED
        sync_state.error_message = error_message

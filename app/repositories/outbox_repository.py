from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.domain.enums import OutboxEventType, OutboxEventStatus
from app.models.models import Outbox


class OutboxRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        outbox_id: UUID,
        event_type: OutboxEventType = OutboxEventType.TICKET_PURCHASED,
        payload: dict,
        status: OutboxEventStatus = OutboxEventStatus.PENDING,
    ) -> None:
        created_at = datetime.now(timezone.utc)
        values = {
            "id": outbox_id,
            "event_type": event_type,
            "payload": payload,
            "status": status,
            "created_at": created_at,
        }
        stmt = insert(Outbox).values(**values)
        await self._session.execute(stmt)

    async def list_pending(self) -> list[Outbox]:
        stmt = select(Outbox).where(Outbox.status == OutboxEventStatus.PENDING).order_by(Outbox.created_at.asc())
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def mark_sent(self, outbox_id: UUID) -> None:
        stmt = update(Outbox).where(Outbox.id == outbox_id).values(status=OutboxEventStatus.SENT)
        await self._session.execute(stmt)
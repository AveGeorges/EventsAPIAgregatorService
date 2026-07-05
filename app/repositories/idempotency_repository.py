from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Idempotency


class IdempotencyRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        idempotency_key: str,
        ticket_id: UUID,
        request_hash: str,
    ) -> None:
        created_at = datetime.now(timezone.utc)
        values = {
            "idempotency_key": idempotency_key,
            "ticket_id": ticket_id,
            "request_hash": request_hash,
            "created_at": created_at,
        }
        stmt = insert(Idempotency).values(**values)
        await self._session.execute(stmt)

    async def get_by_key(self, idempotency_key: str) -> Idempotency | None:
        stmt = select(Idempotency).where(Idempotency.idempotency_key == idempotency_key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_by_ticket_id(self, ticket_id: UUID) -> None:
        stmt = delete(Idempotency).where(Idempotency.ticket_id == ticket_id)
        await self._session.execute(stmt)

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Ticket


class TicketRepository:
    @staticmethod
    async def upsert(
        session: AsyncSession,
        *,
        ticket_id: UUID,
        event_id: UUID,
        seat: str,
        first_name: str,
        last_name: str,
        email: str,
    ) -> None:
        created_at = datetime.now(timezone.utc)
        values = {
            "ticket_id": ticket_id,
            "event_id": event_id,
            "seat": seat,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "created_at": created_at,
        }
        stmt = insert(Ticket).values(**values).on_conflict_do_update(
            constraint="uq_tickets_event_id_seat",
            set_={
                "ticket_id": ticket_id,
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
                "created_at": created_at,
            },
        )
        await session.execute(stmt)

    @staticmethod
    async def get_by_ticket_id(session: AsyncSession, ticket_id: UUID) -> Ticket | None:
        stmt = select(Ticket).where(Ticket.ticket_id == ticket_id)
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def delete(session: AsyncSession, ticket_id: UUID) -> None:
        stmt = delete(Ticket).where(Ticket.ticket_id == ticket_id)
        await session.execute(stmt)

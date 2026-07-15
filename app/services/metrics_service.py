from sqlalchemy.ext.asyncio import AsyncSession

from app.core.metrics import EVENTS_TOTAL, TICKETS_CANCELLED_TOTAL, TICKETS_CREATED_TOTAL
from app.repositories.event_repository import EventRepository
from app.repositories.ticket_repository import TicketRepository


async def refresh_database_gauges(session: AsyncSession) -> None:
    event_repo = EventRepository(session)
    ticket_repo = TicketRepository(session)

    events_count = await event_repo.count()
    tickets_count = await ticket_repo.count()
    tickets_cancelled = await ticket_repo.count_cancelled()

    EVENTS_TOTAL.set(events_count)
    TICKETS_CREATED_TOTAL.set(tickets_count)
    TICKETS_CANCELLED_TOTAL.set(tickets_cancelled)

import asyncio

from fastapi import APIRouter, Depends
from prometheus_client import REGISTRY, generate_latest
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.core.metrics import EVENTS_TOTAL, TICKETS_CANCELLED_TOTAL, TICKETS_CREATED_TOTAL
from app.db.session import get_db
from app.repositories.event_repository import EventRepository
from app.repositories.ticket_repository import TicketRepository

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics(db: AsyncSession = Depends(get_db)) -> Response:
    event_repo = EventRepository(db)
    ticket_repo = TicketRepository(db)

    events_count, tickets_count, tickets_cancelled = await asyncio.gather(
        event_repo.count(),
        ticket_repo.count(),
        ticket_repo.count_cancelled(),
    )

    EVENTS_TOTAL.set(events_count)
    TICKETS_CREATED_TOTAL.set(tickets_count)
    TICKETS_CANCELLED_TOTAL.set(tickets_cancelled)

    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )

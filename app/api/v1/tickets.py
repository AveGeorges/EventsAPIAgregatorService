from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.events_provider.client import create_events_provider_client
from app.schemas.ticket import (
    TicketCancelResponseSchema,
    TicketCreateSchema,
    TicketResponseSchema,
)
from app.services.ticket_service import TicketService

router = APIRouter(tags=["tickets"])


@router.post("/tickets", response_model=TicketResponseSchema, status_code=201)
async def create_ticket(
    payload: TicketCreateSchema,
    db: AsyncSession = Depends(get_db),
) -> TicketResponseSchema:
    provider_client = create_events_provider_client()
    try:
        return await TicketService.create_ticket(db, payload, provider_client=provider_client)
    finally:
        await provider_client.aclose()


@router.delete("/tickets/{ticket_id}", response_model=TicketCancelResponseSchema)
async def cancel_ticket(
    ticket_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> TicketCancelResponseSchema:
    provider_client = create_events_provider_client()
    try:
        return await TicketService.cancel_ticket(db, ticket_id, provider_client=provider_client)
    finally:
        await provider_client.aclose()

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import EventNotFound, TicketNotFound
from app.integrations.events_provider.client import EventsProviderClient
from app.integrations.events_provider.schemas import ProviderRegisterRequestSchema
from app.repositories.event_repository import EventRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCreateSchema, TicketResponseSchema
from app.services.seats_service import SeatsService


class TicketService:
    @staticmethod
    async def create_ticket(
        session: AsyncSession,
        payload: TicketCreateSchema,
        *,
        provider_client: EventsProviderClient,
    ) -> TicketResponseSchema:
        event = await EventRepository.get_by_id(session, payload.event_id)
        if event is None:
            raise EventNotFound(payload.event_id)

        provider_payload = ProviderRegisterRequestSchema(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=str(payload.email),
            seat=payload.seat,
        )
        provider_response = await provider_client.register(payload.event_id, provider_payload)

        await TicketRepository.upsert(
            session,
            ticket_id=provider_response.ticket_id,
            event_id=payload.event_id,
            seat=payload.seat,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=str(payload.email),
        )
        SeatsService.invalidate(payload.event_id)
        await session.commit()

        return TicketResponseSchema(
            ticket_id=provider_response.ticket_id,
            event_id=payload.event_id,
            seat=payload.seat,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
        )

    @staticmethod
    async def cancel_ticket(
        session: AsyncSession,
        ticket_id: UUID,
        *,
        provider_client: EventsProviderClient,
    ) -> None:
        ticket = await TicketRepository.get_by_ticket_id(session, ticket_id)
        if ticket is None:
            raise TicketNotFound(ticket_id)

        await provider_client.unregister(ticket.event_id, ticket_id)
        await TicketRepository.delete(session, ticket_id)
        SeatsService.invalidate(ticket.event_id)
        await session.commit()

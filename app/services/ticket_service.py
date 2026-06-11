from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import EventNotFound, TicketNotFound
from app.integrations.events_provider.client import EventsProviderClient
from app.integrations.events_provider.schemas import ProviderRegisterRequestSchema
from app.repositories.event_repository import EventRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import TicketCancelResponseSchema, TicketCreateSchema, TicketResponseSchema
from app.services.seats_service import SeatsService


class TicketService:
    def __init__(
        self,
        session: AsyncSession,
        provider_client: EventsProviderClient,
        *,
        seats_service: SeatsService | None = None,
    ) -> None:
        self._session = session
        self._provider_client = provider_client
        self._event_repo = EventRepository(session)
        self._ticket_repo = TicketRepository(session)
        self._seats_service = seats_service or SeatsService(session)

    async def create_ticket(self, payload: TicketCreateSchema) -> TicketResponseSchema:
        event = await self._event_repo.get_by_id(payload.event_id)
        if event is None:
            raise EventNotFound(payload.event_id)

        provider_payload = ProviderRegisterRequestSchema(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=str(payload.email),
            seat=payload.seat,
        )
        provider_response = await self._provider_client.register(payload.event_id, provider_payload)

        await self._ticket_repo.upsert(
            ticket_id=provider_response.ticket_id,
            event_id=payload.event_id,
            seat=payload.seat,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=str(payload.email),
        )
        self._seats_service.invalidate(payload.event_id)
        await self._session.commit()

        return TicketResponseSchema(
            ticket_id=provider_response.ticket_id,
            event_id=payload.event_id,
            seat=payload.seat,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
        )

    async def cancel_ticket(self, ticket_id: UUID) -> TicketCancelResponseSchema:
        ticket = await self._ticket_repo.get_by_ticket_id(ticket_id)
        if ticket is None:
            raise TicketNotFound(ticket_id)

        provider_response = await self._provider_client.unregister(ticket.event_id, ticket_id)
        await self._ticket_repo.delete(ticket_id)
        self._seats_service.invalidate(ticket.event_id)
        await self._session.commit()
        return TicketCancelResponseSchema(success=provider_response.success)

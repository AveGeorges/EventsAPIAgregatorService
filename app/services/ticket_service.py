from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.idempotency import compute_request_hash
from app.domain.exceptions import EventNotFound, IdempotencyConflict, TicketNotFound
from app.integrations.events_provider.client import EventsProviderClient
from app.integrations.events_provider.schemas import ProviderRegisterRequestSchema
from app.repositories.event_repository import EventRepository
from app.repositories.idempotency_repository import IdempotencyRepository
from app.repositories.outbox_repository import OutboxRepository
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
        self._outbox_repo = OutboxRepository(session)
        self._idempotency_repo = IdempotencyRepository(session)
        self._seats_service = seats_service or SeatsService(session)

    async def create_ticket(self, payload: TicketCreateSchema) -> TicketResponseSchema:
        request_hash = compute_request_hash(payload)

        event = await self._event_repo.get_by_id(payload.event_id)
        if event is None:
            raise EventNotFound(payload.event_id)

        if payload.idempotency_key is not None:
            existing_key = await self._idempotency_repo.get_by_key(payload.idempotency_key)
            if existing_key is not None:
                if existing_key.request_hash != request_hash:
                    raise IdempotencyConflict()

                ticket = await self._ticket_repo.get_by_ticket_id(existing_key.ticket_id)
                if ticket is None:
                    raise TicketNotFound(existing_key.ticket_id)

                return TicketResponseSchema(
                    ticket_id=ticket.ticket_id,
                    event_id=ticket.event_id,
                    seat=ticket.seat,
                    first_name=ticket.first_name,
                    last_name=ticket.last_name,
                    email=ticket.email,
                )

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

        await self._outbox_repo.create(
            outbox_id=provider_response.ticket_id,
            payload={
                "ticket_id": str(provider_response.ticket_id),
                "message": f"Вы успешно зарегистрированы на мероприятие - {event.name}",
                "notification_idempotency_key": (
                    payload.idempotency_key or f"ticket-{provider_response.ticket_id}"
                ),
            },
        )

        if payload.idempotency_key is not None:
            await self._idempotency_repo.create(
                idempotency_key=payload.idempotency_key,
                ticket_id=provider_response.ticket_id,
                request_hash=request_hash,
            )

        await self._session.commit()

        self._seats_service.invalidate(payload.event_id)

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
        await self._idempotency_repo.delete_by_ticket_id(ticket_id)
        await self._outbox_repo.delete_by_id(ticket_id)
        await self._ticket_repo.delete(ticket_id)
        self._seats_service.invalidate(ticket.event_id)
        await self._session.commit()
        return TicketCancelResponseSchema(success=provider_response.success)

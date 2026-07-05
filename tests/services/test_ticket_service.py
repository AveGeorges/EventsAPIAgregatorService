from unittest.mock import AsyncMock, MagicMock
from uuid import UUID

import pytest

from app.domain.exceptions import EventNotFound, TicketNotFound
from app.integrations.events_provider.schemas import (
    ProviderRegisterResponseSchema,
    ProviderUnregisterResponseSchema,
)
from app.schemas.ticket import TicketCreateSchema, TicketResponseSchema
from app.services.seats_service import SeatsService
from app.services.ticket_service import TicketService

EVENT_ID = UUID("550e8400-e29b-41d4-a716-446655440000")
TICKET_ID = UUID("750e8400-e29b-41d4-a716-446655440002")


def sample_create_payload() -> TicketCreateSchema:
    return TicketCreateSchema(
        event_id=EVENT_ID,
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
        seat="A15",
    )


@pytest.mark.asyncio
async def test_create_ticket_raises_not_found_when_event_missing():
    session = AsyncMock()
    provider_client = AsyncMock()
    service = TicketService(session, provider_client)
    service._event_repo = MagicMock()
    service._event_repo.get_by_id = AsyncMock(return_value=None)

    with pytest.raises(EventNotFound):
        await service.create_ticket(sample_create_payload())

    provider_client.register.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_create_ticket_registers_with_provider_and_saves_locally():
    session = AsyncMock()
    provider_client = AsyncMock()
    provider_client.register.return_value = ProviderRegisterResponseSchema(ticket_id=TICKET_ID)
    payload = sample_create_payload()

    service = TicketService(session, provider_client)
    service._event_repo = MagicMock()
    service._event_repo.get_by_id = AsyncMock(return_value=MagicMock())
    service._ticket_repo = MagicMock()
    service._ticket_repo.upsert = AsyncMock()
    mock_seats_service = MagicMock(spec=SeatsService)
    service._seats_service = mock_seats_service

    result = await service.create_ticket(payload)

    assert result == TicketResponseSchema(
        ticket_id=TICKET_ID,
        event_id=EVENT_ID,
        seat="A15",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
    )
    provider_client.register.assert_awaited_once()
    service._ticket_repo.upsert.assert_awaited_once_with(
        ticket_id=TICKET_ID,
        event_id=EVENT_ID,
        seat="A15",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
    )
    mock_seats_service.invalidate.assert_called_once_with(EVENT_ID)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_cancel_ticket_raises_not_found_when_ticket_missing():
    session = AsyncMock()
    provider_client = AsyncMock()
    service = TicketService(session, provider_client)
    service._ticket_repo = MagicMock()
    service._ticket_repo.get_by_ticket_id = AsyncMock(return_value=None)

    with pytest.raises(TicketNotFound):
        await service.cancel_ticket(TICKET_ID)

    provider_client.unregister.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_cancel_ticket_unregisters_with_provider_and_deletes_locally():
    ticket = MagicMock()
    ticket.event_id = EVENT_ID
    session = AsyncMock()
    provider_client = AsyncMock()
    provider_client.unregister.return_value = ProviderUnregisterResponseSchema(success=True)

    service = TicketService(session, provider_client)
    service._ticket_repo = MagicMock()
    service._ticket_repo.get_by_ticket_id = AsyncMock(return_value=ticket)
    service._ticket_repo.delete = AsyncMock()
    service._idempotency_repo = MagicMock()
    service._idempotency_repo.delete_by_ticket_id = AsyncMock()
    service._outbox_repo = MagicMock()
    service._outbox_repo.delete_by_id = AsyncMock()
    mock_seats_service = MagicMock(spec=SeatsService)
    service._seats_service = mock_seats_service

    result = await service.cancel_ticket(TICKET_ID)

    assert result.success is True
    provider_client.unregister.assert_awaited_once_with(EVENT_ID, TICKET_ID)
    service._idempotency_repo.delete_by_ticket_id.assert_awaited_once_with(TICKET_ID)
    service._outbox_repo.delete_by_id.assert_awaited_once_with(TICKET_ID)
    service._ticket_repo.delete.assert_awaited_once_with(TICKET_ID)
    mock_seats_service.invalidate.assert_called_once_with(EVENT_ID)
    session.commit.assert_awaited_once()

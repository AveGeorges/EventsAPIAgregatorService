from unittest.mock import AsyncMock, MagicMock, patch
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
@patch("app.services.ticket_service.EventRepository.get_by_id", new_callable=AsyncMock)
async def test_create_ticket_raises_not_found_when_event_missing(mock_get_by_id):
    mock_get_by_id.return_value = None
    session = AsyncMock()
    provider_client = AsyncMock()

    with pytest.raises(EventNotFound):
        await TicketService.create_ticket(
            session,
            sample_create_payload(),
            provider_client=provider_client,
        )

    provider_client.register.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
@patch.object(SeatsService, "invalidate")
@patch("app.services.ticket_service.TicketRepository.upsert", new_callable=AsyncMock)
@patch("app.services.ticket_service.EventRepository.get_by_id", new_callable=AsyncMock)
async def test_create_ticket_registers_with_provider_and_saves_locally(
    mock_get_by_id,
    mock_upsert,
    mock_invalidate,
):
    mock_get_by_id.return_value = MagicMock()
    provider_client = AsyncMock()
    provider_client.register.return_value = ProviderRegisterResponseSchema(ticket_id=TICKET_ID)
    session = AsyncMock()
    payload = sample_create_payload()

    result = await TicketService.create_ticket(
        session,
        payload,
        provider_client=provider_client,
    )

    assert result == TicketResponseSchema(
        ticket_id=TICKET_ID,
        event_id=EVENT_ID,
        seat="A15",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
    )
    provider_client.register.assert_awaited_once()
    mock_upsert.assert_awaited_once_with(
        session,
        ticket_id=TICKET_ID,
        event_id=EVENT_ID,
        seat="A15",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
    )
    mock_invalidate.assert_called_once_with(EVENT_ID)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.ticket_service.TicketRepository.get_by_ticket_id", new_callable=AsyncMock)
async def test_cancel_ticket_raises_not_found_when_ticket_missing(mock_get_by_ticket_id):
    mock_get_by_ticket_id.return_value = None
    session = AsyncMock()
    provider_client = AsyncMock()

    with pytest.raises(TicketNotFound):
        await TicketService.cancel_ticket(
            session,
            TICKET_ID,
            provider_client=provider_client,
        )

    provider_client.unregister.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
@patch.object(SeatsService, "invalidate")
@patch("app.services.ticket_service.TicketRepository.delete", new_callable=AsyncMock)
@patch("app.services.ticket_service.TicketRepository.get_by_ticket_id", new_callable=AsyncMock)
async def test_cancel_ticket_unregisters_with_provider_and_deletes_locally(
    mock_get_by_ticket_id,
    mock_delete,
    mock_invalidate,
):
    ticket = MagicMock()
    ticket.event_id = EVENT_ID
    mock_get_by_ticket_id.return_value = ticket
    session = AsyncMock()
    provider_client = AsyncMock()
    provider_client.unregister.return_value = ProviderUnregisterResponseSchema(success=True)

    result = await TicketService.cancel_ticket(
        session,
        TICKET_ID,
        provider_client=provider_client,
    )

    assert result.success is True

    provider_client.unregister.assert_awaited_once_with(EVENT_ID, TICKET_ID)
    mock_delete.assert_awaited_once_with(session, TICKET_ID)
    mock_invalidate.assert_called_once_with(EVENT_ID)
    session.commit.assert_awaited_once()

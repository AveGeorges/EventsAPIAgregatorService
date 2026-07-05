from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
import respx
from httpx import AsyncClient, Response
from sqlalchemy import select

from app.domain.exceptions import EventNotFound, TicketNotFound
from app.models.models import Idempotency, Outbox, Ticket
from app.schemas.ticket import TicketCreateSchema, TicketResponseSchema
from app.services.seats_service import SeatsService
from app.services.ticket_service import TicketService
from tests.integrations.events_provider.conftest import EVENT_ID, TICKET_ID, provider_url
from tests.test_events_api import seed_event


def sample_ticket_response() -> TicketResponseSchema:
    return TicketResponseSchema(
        ticket_id=TICKET_ID,
        event_id=EVENT_ID,
        seat="A15",
        first_name="Иван",
        last_name="Иванов",
        email="ivan@example.com",
    )


def sample_create_body() -> dict:
    return {
        "event_id": str(EVENT_ID),
        "first_name": "Иван",
        "last_name": "Иванов",
        "email": "ivan@example.com",
        "seat": "A15",
    }


@patch.object(TicketService, "create_ticket", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_create_ticket_http_returns_service_response(
    mock_create_ticket, http_client: AsyncClient
):
    mock_create_ticket.return_value = sample_ticket_response()

    response = await http_client.post("/api/tickets", json=sample_create_body())

    assert response.status_code == 201
    body = response.json()
    assert body["ticket_id"] == str(TICKET_ID)
    assert body["seat"] == "A15"
    mock_create_ticket.assert_awaited_once()
    assert mock_create_ticket.await_args.args[0] == TicketCreateSchema.model_validate(
        sample_create_body()
    )


@patch.object(TicketService, "create_ticket", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_create_ticket_http_returns_404_when_event_missing(
    mock_create_ticket, http_client: AsyncClient
):
    mock_create_ticket.side_effect = EventNotFound(EVENT_ID)

    response = await http_client.post("/api/tickets", json=sample_create_body())

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "event_not_found"


@patch.object(TicketService, "cancel_ticket", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_cancel_ticket_http_returns_success(mock_cancel_ticket, http_client: AsyncClient):
    from app.schemas.ticket import TicketCancelResponseSchema

    mock_cancel_ticket.return_value = TicketCancelResponseSchema(success=True)

    response = await http_client.delete(f"/api/tickets/{TICKET_ID}")

    assert response.status_code == 200
    assert response.json() == {"success": True}
    mock_cancel_ticket.assert_awaited_once()


@patch.object(TicketService, "cancel_ticket", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_cancel_ticket_http_returns_404(mock_cancel_ticket, http_client: AsyncClient):
    mock_cancel_ticket.side_effect = TicketNotFound(TICKET_ID)

    response = await http_client.delete(f"/api/tickets/{TICKET_ID}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "ticket_not_found"


@pytest.mark.asyncio
async def test_create_ticket_registers_with_provider_and_persists(
    client: AsyncClient,
    db_session,
):
    SeatsService(db_session).invalidate(EVENT_ID)
    await seed_event(db_session, event_time="2026-06-07T17:00:00+00:00")

    with respx.mock:
        route = respx.post(provider_url("api", "events", EVENT_ID, "register")).mock(
            return_value=Response(201, json={"ticket_id": str(TICKET_ID)})
        )

        response = await client.post("/api/tickets", json=sample_create_body())

    assert response.status_code == 201
    assert response.json()["ticket_id"] == str(TICKET_ID)
    assert route.call_count == 1

    result = await db_session.execute(select(Ticket).where(Ticket.ticket_id == TICKET_ID))
    ticket = result.scalar_one()
    assert ticket.seat == "A15"
    assert ticket.email == "ivan@example.com"


@pytest.mark.asyncio
async def test_create_ticket_invalidates_seats_cache(client: AsyncClient, db_session):
    SeatsService(db_session).invalidate(EVENT_ID)
    await seed_event(db_session, event_time="2026-06-07T17:00:00+00:00")

    with respx.mock:
        respx.post(provider_url("api", "events", EVENT_ID, "register")).mock(
            return_value=Response(201, json={"ticket_id": str(TICKET_ID)})
        )
        seats_route = respx.get(provider_url("api", "events", EVENT_ID, "seats")).mock(
            return_value=Response(200, json={"seats": ["A1"]})
        )

        await client.get(f"/api/events/{EVENT_ID}/seats")
        await client.post("/api/tickets", json=sample_create_body())
        first = await client.get(f"/api/events/{EVENT_ID}/seats")
        second = await client.get(f"/api/events/{EVENT_ID}/seats")

    assert first.status_code == 200
    assert second.status_code == 200
    assert seats_route.call_count == 2


@pytest.mark.asyncio
async def test_cancel_ticket_unregisters_and_removes_local_record(
    client: AsyncClient,
    db_session,
):
    SeatsService(db_session).invalidate(EVENT_ID)
    await seed_event(db_session, event_time="2026-06-07T17:00:00+00:00")

    with respx.mock:
        respx.post(provider_url("api", "events", EVENT_ID, "register")).mock(
            return_value=Response(201, json={"ticket_id": str(TICKET_ID)})
        )
        await client.post("/api/tickets", json=sample_create_body())

        route = respx.delete(provider_url("api", "events", EVENT_ID, "unregister")).mock(
            return_value=Response(200, json={"success": True})
        )

        response = await client.delete(f"/api/tickets/{TICKET_ID}")

    assert response.status_code == 200
    assert response.json() == {"success": True}
    assert route.call_count == 1
    body = route.calls[0].request.read().decode()
    assert str(TICKET_ID) in body
    assert "ticket_id" in body

    result = await db_session.execute(select(Ticket).where(Ticket.ticket_id == TICKET_ID))
    assert result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_cancel_ticket_removes_idempotency_and_outbox(
    client: AsyncClient,
    db_session,
):
    SeatsService(db_session).invalidate(EVENT_ID)
    await seed_event(db_session, event_time="2026-06-07T17:00:00+00:00")
    idempotency_key = "cancel-cleanup-key"

    with respx.mock:
        respx.post(provider_url("api", "events", EVENT_ID, "register")).mock(
            return_value=Response(201, json={"ticket_id": str(TICKET_ID)})
        )
        create_response = await client.post(
            "/api/tickets",
            json={**sample_create_body(), "idempotency_key": idempotency_key},
        )
        assert create_response.status_code == 201

        idempotency_result = await db_session.execute(
            select(Idempotency).where(Idempotency.idempotency_key == idempotency_key)
        )
        assert idempotency_result.scalar_one_or_none() is not None

        outbox_result = await db_session.execute(select(Outbox).where(Outbox.id == TICKET_ID))
        assert outbox_result.scalar_one_or_none() is not None

        respx.delete(provider_url("api", "events", EVENT_ID, "unregister")).mock(
            return_value=Response(200, json={"success": True})
        )

        response = await client.delete(f"/api/tickets/{TICKET_ID}")

    assert response.status_code == 200
    assert response.json() == {"success": True}

    ticket_result = await db_session.execute(select(Ticket).where(Ticket.ticket_id == TICKET_ID))
    assert ticket_result.scalar_one_or_none() is None

    idempotency_result = await db_session.execute(
        select(Idempotency).where(Idempotency.idempotency_key == idempotency_key)
    )
    assert idempotency_result.scalar_one_or_none() is None

    outbox_result = await db_session.execute(select(Outbox).where(Outbox.id == TICKET_ID))
    assert outbox_result.scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_create_ticket_after_cancel_succeeds(
    client: AsyncClient,
    db_session,
):
    SeatsService(db_session).invalidate(EVENT_ID)
    await seed_event(db_session, event_time="2026-06-07T17:00:00+00:00")
    idempotency_key = "recreate-after-cancel"

    with respx.mock:
        respx.post(provider_url("api", "events", EVENT_ID, "register")).mock(
            return_value=Response(201, json={"ticket_id": str(TICKET_ID)})
        )
        first_create = await client.post(
            "/api/tickets",
            json={**sample_create_body(), "idempotency_key": idempotency_key},
        )
        assert first_create.status_code == 201

        respx.delete(provider_url("api", "events", EVENT_ID, "unregister")).mock(
            return_value=Response(200, json={"success": True})
        )
        cancel_response = await client.delete(f"/api/tickets/{TICKET_ID}")
        assert cancel_response.status_code == 200

        second_create = await client.post(
            "/api/tickets",
            json={**sample_create_body(), "idempotency_key": idempotency_key},
        )

    assert second_create.status_code == 201
    assert second_create.json()["ticket_id"] == str(TICKET_ID)


@pytest.mark.asyncio
async def test_create_ticket_returns_400_when_provider_rejects_seat(
    client: AsyncClient,
    db_session,
):
    await seed_event(db_session, event_time="2026-06-07T17:00:00+00:00")

    with respx.mock:
        respx.post(provider_url("api", "events", EVENT_ID, "register")).mock(
            return_value=Response(400, json={"detail": "Seat already taken"})
        )

        response = await client.post("/api/tickets", json=sample_create_body())

    assert response.status_code == 400
    assert response.json()["detail"] == "Seat already taken"


@pytest.mark.asyncio
async def test_create_ticket_returns_404_for_unknown_event(client: AsyncClient):
    unknown_id = uuid4()
    body = {**sample_create_body(), "event_id": str(unknown_id)}

    response = await client.post("/api/tickets", json=body)

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "event_not_found"


@pytest.mark.asyncio
async def test_create_ticket_returns_400_for_invalid_body(http_client: AsyncClient):
    response = await http_client.post(
        "/api/tickets",
        json={
            "event_id": "not-a-uuid",
            "first_name": "Ivan",
            "last_name": "Ivanov",
            "email": "x",
            "seat": "A1",
        },
    )

    assert response.status_code == 400
    assert "detail" in response.json()

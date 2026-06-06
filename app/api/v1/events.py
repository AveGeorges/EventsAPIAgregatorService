from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.events_provider.client import create_events_provider_client
from app.schemas.event import EventDetailSchema, EventsPageResponseSchema
from app.schemas.seats import SeatsResponseSchema
from app.services.event_service import EventService
from app.services.seats_service import SeatsService

router = APIRouter(tags=["events"])


@router.get("/events", response_model=EventsPageResponseSchema)
async def list_events(
    request: Request,
    db: AsyncSession = Depends(get_db),
    date_from: date | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1),
) -> EventsPageResponseSchema:
    events_base_url = str(request.url.replace(query=""))
    return await EventService.list_events(
        db,
        events_base_url=events_base_url,
        date_from=date_from,
        page=page,
        page_size=page_size,
    )


@router.get("/events/{event_id}/seats", response_model=SeatsResponseSchema)
async def get_event_seats(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SeatsResponseSchema:
    provider_client = create_events_provider_client()
    try:
        return await SeatsService.get_seats(
            db,
            event_id,
            provider_client=provider_client,
        )
    finally:
        await provider_client.aclose()


@router.get("/events/{event_id}", response_model=EventDetailSchema)
async def get_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EventDetailSchema:
    return await EventService.get_event(db, event_id)

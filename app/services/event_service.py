from datetime import date
from urllib.parse import urlencode
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.exceptions import EventNotFound
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventDetailSchema, EventListItemSchema, EventsPageResponseSchema


class EventService:
    @staticmethod
    async def list_events(
        session: AsyncSession,
        *,
        events_base_url: str,
        date_from: date | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> EventsPageResponseSchema:
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20

        offset = (page - 1) * page_size
        total = await EventRepository.count(session, date_from=date_from)
        events = await EventRepository.list_page(
            session,
            date_from=date_from,
            offset=offset,
            limit=page_size,
        )

        next_url = None
        if page * page_size < total:
            next_url = EventService._build_page_url(
                events_base_url,
                page=page + 1,
                page_size=page_size,
                date_from=date_from,
            )

        previous_url = None
        if page > 1:
            previous_url = EventService._build_page_url(
                events_base_url,
                page=page - 1,
                page_size=page_size,
                date_from=date_from,
            )

        return EventsPageResponseSchema(
            count=total,
            next=next_url,
            previous=previous_url,
            results=[EventListItemSchema.model_validate(event) for event in events],
        )

    @staticmethod
    async def get_event(session: AsyncSession, event_id: UUID) -> EventDetailSchema:
        event = await EventRepository.get_by_id(session, event_id)
        if event is None:
            raise EventNotFound(event_id)
        return EventDetailSchema.model_validate(event)

    @staticmethod
    def _build_page_url(
        base_url: str,
        *,
        page: int,
        page_size: int,
        date_from: date | None,
    ) -> str:
        query: dict[str, str | int] = {"page": page, "page_size": page_size}
        if date_from is not None:
            query["date_from"] = date_from.isoformat()
        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}{urlencode(query)}"

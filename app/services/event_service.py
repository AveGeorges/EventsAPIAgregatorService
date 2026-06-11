from datetime import date
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.url_utils import append_query
from app.domain.exceptions import EventNotFound
from app.repositories.event_repository import EventRepository
from app.schemas.event import EventDetailSchema, EventListItemSchema, EventsPageResponseSchema


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
    return append_query(base_url, query)


class EventService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._event_repo = EventRepository(session)

    async def list_events(
        self,
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
        total = await self._event_repo.count(date_from=date_from)
        events = await self._event_repo.list_page(
            date_from=date_from,
            offset=offset,
            limit=page_size,
        )

        next_url = None
        if page * page_size < total:
            next_url = _build_page_url(
                events_base_url,
                page=page + 1,
                page_size=page_size,
                date_from=date_from,
            )

        previous_url = None
        if page > 1:
            previous_url = _build_page_url(
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

    async def get_event(self, event_id: UUID) -> EventDetailSchema:
        event = await self._event_repo.get_by_id(event_id)
        if event is None:
            raise EventNotFound(event_id)
        return EventDetailSchema.model_validate(event)

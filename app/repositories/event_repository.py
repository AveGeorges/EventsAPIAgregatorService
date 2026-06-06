from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.integrations.events_provider.schemas import ProviderEventSchema
from app.models.models import Event


class EventRepository:
    @staticmethod
    async def upsert(session: AsyncSession, event: ProviderEventSchema) -> None:
        values = {
            "id": event.id,
            "name": event.name,
            "place_id": event.place.id,
            "event_time": event.event_time,
            "registration_deadline": event.registration_deadline,
            "status": event.status.value,
            "number_of_visitors": event.number_of_visitors,
            "created_at": event.created_at,
            "changed_at": event.changed_at,
            "status_changed_at": event.status_changed_at,
        }
        stmt = insert(Event).values(**values).on_conflict_do_update(
            index_elements=[Event.id],
            set_={
                "name": event.name,
                "place_id": event.place.id,
                "event_time": event.event_time,
                "registration_deadline": event.registration_deadline,
                "status": event.status.value,
                "number_of_visitors": event.number_of_visitors,
                "changed_at": event.changed_at,
                "status_changed_at": event.status_changed_at,
            },
        )
        await session.execute(stmt)

    @staticmethod
    async def count(session: AsyncSession, *, date_from: date | None = None) -> int:
        stmt = select(func.count()).select_from(Event)
        if date_from is not None:
            stmt = stmt.where(Event.event_time >= EventRepository._start_of_day(date_from))
        result = await session.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def list_page(
        session: AsyncSession,
        *,
        date_from: date | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> list[Event]:
        stmt = (
            select(Event)
            .options(joinedload(Event.place))
            .order_by(Event.event_time.asc())
            .offset(offset)
            .limit(limit)
        )
        if date_from is not None:
            stmt = stmt.where(Event.event_time >= EventRepository._start_of_day(date_from))
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    @staticmethod
    async def get_by_id(session: AsyncSession, event_id: UUID) -> Event | None:
        stmt = (
            select(Event)
            .options(joinedload(Event.place))
            .where(Event.id == event_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    def _start_of_day(value: date) -> datetime:
        return datetime.combine(value, datetime.min.time(), tzinfo=timezone.utc)

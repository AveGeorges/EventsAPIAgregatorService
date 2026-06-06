from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

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

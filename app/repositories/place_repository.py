from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.events_provider.schemas import ProviderPlaceSchema
from app.models.models import Place


class PlaceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert(self, place: ProviderPlaceSchema) -> None:
        values = {
            "id": place.id,
            "name": place.name,
            "city": place.city,
            "address": place.address,
            "seats_pattern": place.seats_pattern,
            "created_at": place.created_at,
            "changed_at": place.changed_at,
        }
        stmt = insert(Place).values(**values).on_conflict_do_update(
            index_elements=[Place.id],
            set_={
                "name": place.name,
                "city": place.city,
                "address": place.address,
                "seats_pattern": place.seats_pattern,
                "changed_at": place.changed_at,
            },
        )
        await self._session.execute(stmt)

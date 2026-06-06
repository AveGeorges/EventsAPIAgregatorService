from collections.abc import AsyncIterator
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import select

from app.domain.enums import SyncStatus
from app.integrations.events_provider.schemas import ProviderEventSchema
from app.models.models import Event, Place, SyncState
from app.services.event_sync_service import INITIAL_CHANGED_AT, EventSyncService
from tests.integrations.events_provider.conftest import sample_event_payload


class FakeEventsProviderClient:
    def __init__(self, events: list[ProviderEventSchema]) -> None:
        self._events = events

    async def iter_all_events(self, changed_at: date) -> AsyncIterator[ProviderEventSchema]:
        for event in self._events:
            yield event

    async def aclose(self) -> None:
        return None


@pytest.mark.asyncio
async def test_run_sync_persists_events_and_updates_sync_state(db_session):
    provider_event = ProviderEventSchema.model_validate(sample_event_payload())
    service = EventSyncService(db_session, FakeEventsProviderClient([provider_event]))

    result = await service.run_sync()

    assert result.events_synced == 1
    assert result.changed_at == INITIAL_CHANGED_AT
    assert result.last_changed_at == provider_event.changed_at

    sync_state = (await db_session.execute(select(SyncState))).scalar_one()
    assert sync_state.sync_status == SyncStatus.SUCCESS
    assert sync_state.last_changed_at == provider_event.changed_at

    places = (await db_session.execute(select(Place))).scalars().all()
    assert len(places) == 1
    assert places[0].id == provider_event.place.id

    events = (await db_session.execute(select(Event))).scalars().all()
    assert len(events) == 1
    assert events[0].id == provider_event.id


@pytest.mark.asyncio
async def test_run_sync_uses_last_changed_at_on_subsequent_sync(db_session):
    first_event = ProviderEventSchema.model_validate(sample_event_payload())
    second_event = ProviderEventSchema.model_validate(sample_event_payload())
    second_event_changed_at = datetime(2026, 1, 3, 10, 0, tzinfo=timezone.utc)
    second_event = second_event.model_copy(update={"changed_at": second_event_changed_at})

    service = EventSyncService(db_session, FakeEventsProviderClient([first_event]))
    await service.run_sync()

    service = EventSyncService(db_session, FakeEventsProviderClient([second_event]))
    result = await service.run_sync()

    assert result.changed_at == first_event.changed_at.date()
    assert result.events_synced == 1

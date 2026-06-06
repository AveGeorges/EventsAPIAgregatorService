from datetime import date, datetime
from typing import Self

from pydantic import BaseModel, ConfigDict

from app.services.event_sync_service import SyncResult


class SyncTriggerResponse(BaseModel):
    """HTTP-ответ POST /api/sync/trigger."""

    model_config = ConfigDict(from_attributes=True)

    events_synced: int
    changed_at: date
    last_changed_at: datetime | None

    @classmethod
    def from_result(cls, result: SyncResult) -> Self:
        return cls(
            events_synced=result.events_synced,
            changed_at=result.changed_at,
            last_changed_at=result.last_changed_at,
        )

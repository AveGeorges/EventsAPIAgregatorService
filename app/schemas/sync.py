from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class SyncTriggerResponse(BaseModel):
    """HTTP-ответ POST /api/sync/trigger."""

    model_config = ConfigDict(from_attributes=True)

    events_synced: int
    changed_at: date
    last_changed_at: datetime | None

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CapashinoNotificationCreateSchema(BaseModel):
    message: str
    reference_id: str
    idempotency_key: str


class CapashinoNotificationResponseSchema(BaseModel):
    id: UUID
    user_id: UUID
    message: str
    reference_id: str
    created_at: datetime
    idempotency_key: str | None = None
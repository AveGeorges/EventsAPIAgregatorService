from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SeatsResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event_id: UUID
    available_seats: list[str] = Field(default_factory=list)

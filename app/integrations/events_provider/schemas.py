from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EventStatus


class ProviderPlaceSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    city: str
    address: str
    seats_pattern: str
    created_at: datetime
    changed_at: datetime


class ProviderEventSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    place: ProviderPlaceSchema
    event_time: datetime
    registration_deadline: datetime
    status: EventStatus
    number_of_visitors: int
    created_at: datetime
    changed_at: datetime
    status_changed_at: datetime


class ProviderEventsPageSchema(BaseModel):
    next: str | None = None
    previous: str | None = None
    results: list[ProviderEventSchema] = Field(default_factory=list)


class ProviderSeatsSchema(BaseModel):
    event_id: UUID
    available_seats: list[str] = Field(default_factory=list)


class ProviderRegisterRequestSchema(BaseModel):
    first_name: str
    last_name: str
    email: str
    seat: str


class ProviderRegisterResponseSchema(BaseModel):
    ticket_id: UUID


class ProviderUnregisterResponseSchema(BaseModel):
    success: bool

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EventStatus


class PlaceSummarySchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    city: str
    address: str


class PlaceDetailSchema(PlaceSummarySchema):
    seats_pattern: str


class EventBaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    event_time: datetime
    registration_deadline: datetime
    status: EventStatus
    number_of_visitors: int


class EventListItemSchema(EventBaseSchema):
    place: PlaceSummarySchema


class EventDetailSchema(EventBaseSchema):
    place: PlaceDetailSchema


class EventsPageResponseSchema(BaseModel):
    count: int = Field(..., ge=0, description="Общее число событий с учётом фильтров")
    next: str | None = None
    previous: str | None = None
    results: list[EventListItemSchema] = Field(default_factory=list)

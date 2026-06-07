from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TicketCreateSchema(BaseModel):
    event_id: UUID
    first_name: str = Field(..., min_length=1, max_length=255)
    last_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    seat: str = Field(..., min_length=1, max_length=32)


class TicketResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticket_id: UUID
    event_id: UUID
    seat: str
    first_name: str
    last_name: str
    email: EmailStr

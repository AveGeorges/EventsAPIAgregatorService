from datetime import datetime, timezone

from sqlalchemy import (
    UUID,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum as SQLAlchemyEnum

from app.db.base import Base
from app.domain.enums import EventStatus, SyncStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Place(Base):
    __tablename__ = "places"
    __table_args__ = (Index("ix_places_city", "city"),)

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    city = Column(String(255), nullable=False)
    address = Column(String(512), nullable=False)
    seats_pattern = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False)

    events = relationship("Event", back_populates="place")

    def __repr__(self) -> str:
        return f"Place(id={self.id!s}, name={self.name!r}, city={self.city!r})"


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (Index("ix_events_event_time", "event_time"),)

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(255), nullable=False)
    place_id = Column(UUID(as_uuid=True), ForeignKey("places.id"), nullable=False, index=True)
    event_time = Column(DateTime(timezone=True), nullable=False)
    registration_deadline = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        SQLAlchemyEnum(EventStatus, name="event_status", native_enum=False),
        nullable=False,
    )
    number_of_visitors = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), nullable=False)
    changed_at = Column(DateTime(timezone=True), nullable=False)
    status_changed_at = Column(DateTime(timezone=True), nullable=False)

    place = relationship("Place", back_populates="events")
    tickets = relationship("Ticket", back_populates="event")

    def __repr__(self) -> str:
        return f"Event(id={self.id!s}, name={self.name!r}, status={self.status!r})"


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        UniqueConstraint("event_id", "seat", name="uq_tickets_event_id_seat"),
    )

    ticket_id = Column(UUID(as_uuid=True), primary_key=True)
    event_id = Column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    seat = Column(String(32), nullable=False)
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=_utcnow)

    event = relationship("Event", back_populates="tickets")

    def __repr__(self) -> str:
        return (
            f"Ticket(ticket_id={self.ticket_id!s}, event_id={self.event_id!s}, seat={self.seat!r})"
        )


class SyncState(Base):
    """Singleton-строка метаданных синхронизации (id=1)."""

    __tablename__ = "sync_state"

    id = Column(Integer, primary_key=True, default=1)
    last_sync_time = Column(DateTime(timezone=True), nullable=True)
    last_changed_at = Column(DateTime(timezone=True), nullable=True)
    sync_status = Column(
        SQLAlchemyEnum(SyncStatus, name="sync_status", native_enum=False),
        nullable=False,
        default=SyncStatus.IDLE,
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return f"SyncState(status={self.sync_status!r}, last_changed_at={self.last_changed_at!r})"

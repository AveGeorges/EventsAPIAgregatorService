from unittest.mock import patch
from uuid import UUID

from app.schemas.seats import SeatsResponseSchema
from app.services.seats_cache import SeatsCache

EVENT_ID = UUID("550e8400-e29b-41d4-a716-446655440000")


def sample_seats() -> SeatsResponseSchema:
    return SeatsResponseSchema(event_id=EVENT_ID, available_seats=["A1", "A2"])


def test_get_returns_none_on_miss():
    cache = SeatsCache()
    assert cache.get(EVENT_ID) is None


def test_set_and_get():
    cache = SeatsCache(ttl_seconds=30)
    seats = sample_seats()
    cache.set(EVENT_ID, seats)
    assert cache.get(EVENT_ID) == seats


@patch("app.services.seats_cache.monotonic")
def test_get_returns_none_after_ttl(mock_monotonic):
    mock_monotonic.side_effect = [0.0, 0.0, 31.0]
    cache = SeatsCache(ttl_seconds=30)
    cache.set(EVENT_ID, sample_seats())
    assert cache.get(EVENT_ID) is not None
    assert cache.get(EVENT_ID) is None


def test_invalidate_removes_entry():
    cache = SeatsCache()
    cache.set(EVENT_ID, sample_seats())
    cache.invalidate(EVENT_ID)
    assert cache.get(EVENT_ID) is None

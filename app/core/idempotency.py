import hashlib
import json

from app.schemas.ticket import TicketCreateSchema


def compute_request_hash(payload: TicketCreateSchema) -> str:
    """Отпечаток тела регистрации без idempotency_key."""
    data = {
        "email": str(payload.email).strip().lower(),
        "event_id": str(payload.event_id),
        "first_name": payload.first_name.strip(),
        "last_name": payload.last_name.strip(),
        "seat": payload.seat.strip(),
    }
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
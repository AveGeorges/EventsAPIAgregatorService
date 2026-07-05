from uuid import UUID

import pytest

from app.domain.enums import OutboxEventStatus
from app.repositories.outbox_repository import OutboxRepository

OUTBOX_ID = UUID("750e8400-e29b-41d4-a716-446655440002")


@pytest.mark.asyncio
async def test_list_pending_finds_rows_with_lowercase_status(db_session):
    repo = OutboxRepository(db_session)
    await repo.create(
        outbox_id=OUTBOX_ID,
        payload={
            "ticket_id": str(OUTBOX_ID),
            "message": "test",
            "notification_idempotency_key": "key-1",
        },
        status=OutboxEventStatus.PENDING,
    )
    await db_session.commit()

    pending = await repo.list_pending()

    assert len(pending) == 1
    assert pending[0].id == OUTBOX_ID
    assert pending[0].status == OutboxEventStatus.PENDING

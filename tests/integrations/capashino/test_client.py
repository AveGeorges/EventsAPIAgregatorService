import httpx
import pytest
import respx
from httpx import Response

from app.integrations.capashino.client import CapashinoClient
from app.integrations.capashino.schemas import CapashinoNotificationCreateSchema

BASE_URL = "http://capashino.test"


@pytest.mark.asyncio
async def test_create_notification_posts_to_path_without_trailing_slash():
    payload = CapashinoNotificationCreateSchema(
        message="test message",
        reference_id="750e8400-e29b-41d4-a716-446655440002",
        idempotency_key="key-1",
    )

    with respx.mock:
        route = respx.post(f"{BASE_URL}/api/notifications").mock(
            return_value=Response(
                201,
                json={
                    "id": "750e8400-e29b-41d4-a716-446655440002",
                    "user_id": "650e8400-e29b-41d4-a716-446655440001",
                    "message": "test message",
                    "reference_id": "750e8400-e29b-41d4-a716-446655440002",
                    "created_at": "2026-07-05T16:00:00+00:00",
                    "idempotency_key": "key-1",
                },
            )
        )
        respx.post(f"{BASE_URL}/api/notifications/").mock(return_value=Response(404))

        async with CapashinoClient(BASE_URL, "test-key", client=httpx.AsyncClient()) as client:
            await client.create_notification(payload)

    assert route.call_count == 1

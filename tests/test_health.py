import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(http_client: AsyncClient):
    response = await http_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-Request-ID" in response.headers


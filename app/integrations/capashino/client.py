from typing import Any

import httpx

from app.core.config import settings
from app.core.http_utils import _extract_error_message
from app.core.url_utils import join_url, normalize_base_url
from app.integrations.capashino.exceptions import (
    CapashinoBadRequestError,
    CapashinoConflictError,
    CapashinoError,
    CapashinoRateLimitError,
    CapashinoServerError,
    CapashinoUnauthorizedError,
    CapashinoUnprocessableError,
)
from app.integrations.capashino.schemas import (
    CapashinoNotificationCreateSchema,
    CapashinoNotificationResponseSchema,
)


class CapashinoClient:
    """Async HTTP-клиент Capashino API."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = normalize_base_url(base_url)
        self._api_key = api_key
        self._owns_client = client is None
        self._client = client or httpx.AsyncClient(
            base_url=self._base_url,
            headers={"X-API-Key": self._api_key},
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "CapashinoClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def _endpoint(self, *parts: str) -> str:
        return join_url(self._base_url, *parts, trailing_slash=True)

    async def create_notification(
        self,
        payload: CapashinoNotificationCreateSchema,
    ) -> CapashinoNotificationResponseSchema:
        response = await self._request(
            "POST",
            self._endpoint("api", "notifications"),
            absolute=True,
            json=payload.model_dump(mode="json"),
        )
        return CapashinoNotificationResponseSchema.model_validate(response.json())

    async def _request(
        self,
        method: str,
        url: str,
        *,
        absolute: bool = False,
        **kwargs: Any,
    ) -> httpx.Response:
        request_url = url if absolute else url.lstrip("/")
        try:
            response = await self._client.request(method, request_url, **kwargs)
        except httpx.HTTPError as exc:
            raise CapashinoError(f"Capashino request failed: {exc}") from exc

        self._raise_for_status(response)
        return response

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return

        status_code = response.status_code
        message = _extract_error_message(response)

        if status_code == 400:
            raise CapashinoBadRequestError(message, status_code=status_code)
        if status_code == 401:
            raise CapashinoUnauthorizedError(message, status_code=status_code)
        if status_code == 409:
            raise CapashinoConflictError(message, status_code=status_code)
        if status_code == 422:
            raise CapashinoUnprocessableError(message, status_code=status_code)
        if status_code == 429:
            raise CapashinoRateLimitError(message, status_code=status_code)
        if status_code >= 500:
            raise CapashinoServerError(message, status_code=status_code)
        raise CapashinoError(message, status_code=status_code)


def create_capashino_client(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> CapashinoClient:
    return CapashinoClient(
        base_url=base_url or settings.capashino_base_url,
        api_key=api_key or settings.CAPASHINO_API_KEY,
        client=client,
    )

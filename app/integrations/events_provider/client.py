from datetime import date
from typing import Any
from uuid import UUID

import httpx

from app.core.config import settings
from app.core.http_utils import _extract_error_message
from app.core.url_utils import join_url, normalize_base_url
from app.integrations.events_provider.exceptions import (
    EventsProviderAuthError,
    EventsProviderBadRequestError,
    EventsProviderError,
    EventsProviderNotFoundError,
    EventsProviderRateLimitError,
    EventsProviderServerError,
)
from app.integrations.events_provider.paginator import EventsPaginator
from app.integrations.events_provider.schemas import (
    ProviderEventSchema,
    ProviderEventsPageSchema,
    ProviderRegisterRequestSchema,
    ProviderRegisterResponseSchema,
    ProviderSeatsSchema,
    ProviderUnregisterResponseSchema,
)


class EventsProviderClient:
    """Async HTTP-клиент Events Provider API."""

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
            headers={"x-api-key": self._api_key},
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        )

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def __aenter__(self) -> "EventsProviderClient":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()

    def _endpoint(self, *parts: str) -> str:
        return join_url(self._base_url, *parts, trailing_slash=True)

    async def list_events(
        self,
        changed_at: date,
        *,
        page_url: str | None = None,
    ) -> ProviderEventsPageSchema:
        if page_url:
            response = await self._request("GET", page_url, absolute=True)
        else:
            response = await self._request(
                "GET",
                self._endpoint("api", "events"),
                absolute=True,
                params={"changed_at": changed_at.isoformat()},
            )
        return ProviderEventsPageSchema.model_validate(response.json())

    async def get_event(self, event_id: UUID) -> ProviderEventSchema:
        url = self._endpoint("api", "events", event_id)
        response = await self._request("GET", url, absolute=True)
        return ProviderEventSchema.model_validate(response.json())

    async def get_seats(self, event_id: UUID) -> ProviderSeatsSchema:
        response = await self._request(
            "GET",
            self._endpoint("api", "events", event_id, "seats"),
            absolute=True,
        )
        return ProviderSeatsSchema.model_validate(response.json())

    async def register(
        self,
        event_id: UUID,
        payload: ProviderRegisterRequestSchema,
    ) -> ProviderRegisterResponseSchema:
        response = await self._request(
            "POST",
            self._endpoint("api", "events", event_id, "register"),
            absolute=True,
            json=payload.model_dump(mode="json"),
        )
        return ProviderRegisterResponseSchema.model_validate(response.json())

    async def unregister(
        self,
        event_id: UUID,
        ticket_id: UUID,
    ) -> ProviderUnregisterResponseSchema:
        response = await self._request(
            "DELETE",
            self._endpoint("api", "events", event_id, "unregister"),
            absolute=True,
            json={"ticket_id": str(ticket_id)},
        )
        return ProviderUnregisterResponseSchema.model_validate(response.json())

    def paginate_events(self, changed_at: date) -> EventsPaginator:
        return EventsPaginator(self, changed_at)

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
            raise EventsProviderError(f"Events Provider request failed: {exc}") from exc

        self._raise_for_status(response)
        return response

    def _raise_for_status(self, response: httpx.Response) -> None:
        if response.is_success:
            return

        status_code = response.status_code
        message = _extract_error_message(response)

        if status_code == 401:
            raise EventsProviderAuthError(message, status_code=status_code)
        if status_code == 404:
            raise EventsProviderNotFoundError(message, status_code=status_code)
        if status_code == 400:
            raise EventsProviderBadRequestError(message, status_code=status_code)
        if status_code == 429:
            raise EventsProviderRateLimitError(message, status_code=status_code)
        if status_code >= 500:
            raise EventsProviderServerError(message, status_code=status_code)

        raise EventsProviderError(message, status_code=status_code)


def create_events_provider_client(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    client: httpx.AsyncClient | None = None,
) -> EventsProviderClient:
    return EventsProviderClient(
        base_url=base_url or settings.events_provider_base_url,
        api_key=api_key or settings.EVENTS_PROVIDER_API_KEY,
        client=client,
    )

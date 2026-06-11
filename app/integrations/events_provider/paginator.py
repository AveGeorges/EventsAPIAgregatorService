from datetime import date
from typing import TYPE_CHECKING, Self

from app.integrations.events_provider.schemas import ProviderEventSchema

if TYPE_CHECKING:
    from app.integrations.events_provider.client import EventsProviderClient


class EventsPaginator:
    """Async-итератор по всем событиям провайдера с cursor-пагинацией."""

    def __init__(self, client: "EventsProviderClient", changed_at: date) -> None:
        self._client = client
        self._changed_at = changed_at
        self._page_results: list[ProviderEventSchema] = []
        self._index = 0
        self._next_url: str | None = None
        self._initial_page_loaded = False

    def __aiter__(self) -> Self:
        return self

    async def __anext__(self) -> ProviderEventSchema:
        while True:
            if self._index < len(self._page_results):
                event = self._page_results[self._index]
                self._index += 1
                return event
            if not await self._fetch_next_page():
                raise StopAsyncIteration

    async def _fetch_next_page(self) -> bool:
        if self._initial_page_loaded and self._next_url is None:
            return False

        if not self._initial_page_loaded:
            page = await self._client.list_events(self._changed_at)
            self._initial_page_loaded = True
        else:
            page = await self._client.list_events(self._changed_at, page_url=self._next_url)

        self._page_results = page.results
        self._index = 0
        self._next_url = page.next
        return bool(self._page_results) or self._next_url is not None

class EventsProviderError(Exception):
    """Базовая ошибка HTTP-клиента Events Provider."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class EventsProviderNotFoundError(EventsProviderError):
    """Ресурс не найден (404)."""


class EventsProviderAuthError(EventsProviderError):
    """Ошибка аутентификации (401)."""


class EventsProviderBadRequestError(EventsProviderError):
    """Некорректный запрос или бизнес-ошибка провайдера (400)."""


class EventsProviderRateLimitError(EventsProviderError):
    """Превышен лимит запросов (429)."""


class EventsProviderServerError(EventsProviderError):
    """Внутренняя ошибка провайдера (5xx)."""

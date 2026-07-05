class CapashinoError(Exception):
    """Базовая ошибка HTTP-клиента Capashino."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class CapashinoBadRequestError(CapashinoError):
    """Некорректный запрос (400)."""


class CapashinoUnauthorizedError(CapashinoError):
    """Неавторизованный запрос (401)."""


class CapashinoConflictError(CapashinoError):
    """Конфликт (409)."""


class CapashinoUnprocessableError(CapashinoError):
    """Непроцессируемый запрос (422)."""


class CapashinoRateLimitError(CapashinoError):
    """Превышен лимит запросов (429)."""


class CapashinoServerError(CapashinoError):
    """Внутренняя ошибка Capashino (5xx)."""
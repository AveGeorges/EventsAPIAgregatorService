from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.domain.exceptions import DomainError
from app.integrations.events_provider.exceptions import (
    EventsProviderAuthError,
    EventsProviderBadRequestError,
    EventsProviderError,
    EventsProviderNotFoundError,
    EventsProviderRateLimitError,
)


async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": {"code": exc.code, "message": exc.message}},
    )


def _provider_error_status_code(exc: EventsProviderError) -> int:
    if isinstance(exc, EventsProviderNotFoundError):
        return 404
    if isinstance(exc, EventsProviderBadRequestError):
        return 400
    if isinstance(exc, EventsProviderAuthError):
        return 401
    if isinstance(exc, EventsProviderRateLimitError):
        return 429
    if exc.status_code is not None and 400 <= exc.status_code < 500:
        return exc.status_code
    return 502


async def events_provider_error_handler(
    _request: Request, exc: EventsProviderError
) -> JSONResponse:
    return JSONResponse(
        status_code=_provider_error_status_code(exc),
        content={"detail": exc.message},
    )


async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    return JSONResponse(status_code=400, content={"detail": exc.errors()})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(EventsProviderError, events_provider_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)

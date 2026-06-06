from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.domain.exceptions import DomainError
from app.integrations.events_provider.exceptions import EventsProviderError


async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": {"code": exc.code, "message": exc.message}},
    )


async def events_provider_error_handler(
    _request: Request, exc: EventsProviderError
) -> JSONResponse:
    return JSONResponse(status_code=502, content={"detail": exc.message})


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(EventsProviderError, events_provider_error_handler)

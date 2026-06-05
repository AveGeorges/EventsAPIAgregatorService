from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.middleware import RequestIdMiddleware
from app.core.logging import configure_logging


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(title="Events API Agregator Service")

    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)

    @app.get("/api/health")
    async def health_check():
        return {"status": "ok"}

    return app


app = create_app()

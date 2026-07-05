import asyncio
import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

from app.api.exception_handlers import register_exception_handlers
from app.api.middleware import RequestIdMiddleware
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging
from app.services.outbox_worker import run_outbox_worker_loop
from app.services.sync_scheduler import run_scheduled_sync

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler: AsyncIOScheduler | None = None
    outbox_task: asyncio.Task | None = None

    if settings.OUTBOX_WORKER_ENABLED:
        outbox_task = asyncio.create_task(run_outbox_worker_loop())
        logger.info("Outbox worker started")

    if settings.SYNC_CRON_ENABLED:
        scheduler = AsyncIOScheduler(timezone=settings.SYNC_CRON_TIMEZONE)
        scheduler.add_job(
            run_scheduled_sync,
            trigger=CronTrigger(
                hour=settings.SYNC_CRON_HOUR,
                minute=settings.SYNC_CRON_MINUTE,
                timezone=settings.SYNC_CRON_TIMEZONE,
            ),
            id="scheduled_sync",
            replace_existing=True,
        )
        scheduler.start()
        logger.info(
            "Scheduled sync at %02d:%02d %s",
            settings.SYNC_CRON_HOUR,
            settings.SYNC_CRON_MINUTE,
            settings.SYNC_CRON_TIMEZONE,
        )

    yield

    if outbox_task is not None:
        outbox_task.cancel()
        try:
            await outbox_task
        except asyncio.CancelledError:
            pass

    if scheduler is not None:
        scheduler.shutdown(wait=False)


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        lifespan=lifespan,
    )

    app.add_middleware(RequestIdMiddleware)
    register_exception_handlers(app)
    app.include_router(api_router, prefix="/api")

    return app


app = create_app()

import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.integrations.capashino.client import CapashinoClient, create_capashino_client
from app.integrations.capashino.exceptions import (
    CapashinoBadRequestError,
    CapashinoConflictError,
    CapashinoError,
    CapashinoRateLimitError,
    CapashinoServerError,
    CapashinoUnauthorizedError,
    CapashinoUnprocessableError,
)
from app.integrations.capashino.schemas import CapashinoNotificationCreateSchema
from app.repositories.outbox_repository import OutboxRepository

logger = logging.getLogger(__name__)


async def process_outbox_events(
    outbox_repo: OutboxRepository,
    capashino_client: CapashinoClient,
    session: AsyncSession,
) -> None:
    pending = [
        (row.id, dict(row.payload))
        for row in await outbox_repo.list_pending()
    ]
    for outbox_id, payload in pending:
        try:
            await capashino_client.create_notification(
                CapashinoNotificationCreateSchema(
                    message=payload["message"],
                    reference_id=payload["ticket_id"],
                    idempotency_key=payload["notification_idempotency_key"],
                )
            )
            await outbox_repo.mark_sent(outbox_id=outbox_id)
            await session.commit()
        except CapashinoConflictError:
            logger.info(
                "Capashino notification already exists",
                extra={"outbox_id": str(outbox_id)},
            )
            await outbox_repo.mark_sent(outbox_id=outbox_id)
            await session.commit()
        except (
            CapashinoServerError,
            CapashinoUnauthorizedError,
            CapashinoBadRequestError,
            CapashinoUnprocessableError,
            CapashinoRateLimitError,
            CapashinoError,
        ) as exc:
            logger.error(
                "Capashino notification failed, will retry",
                extra={"outbox_id": str(outbox_id), "error": exc.message},
            )
            await session.rollback()
        except Exception:
            logger.exception(
                "Unexpected outbox processing error",
                extra={"outbox_id": str(outbox_id)},
            )
            await session.rollback()


async def run_outbox_worker_loop() -> None:
    while True:
        async with AsyncSessionLocal() as session:
            client = create_capashino_client()
            try:
                await process_outbox_events(
                    OutboxRepository(session),
                    client,
                    session,
                )
            except Exception:
                logger.exception("Outbox worker iteration failed")
            finally:
                await client.aclose()
        await asyncio.sleep(settings.OUTBOX_POLL_INTERVAL_SECONDS)

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.integrations.events_provider.client import create_events_provider_client
from app.schemas.sync import SyncTriggerResponse
from app.services.event_sync_service import EventSyncService

router = APIRouter(tags=["sync"])


@router.post("/sync/trigger", response_model=SyncTriggerResponse)
async def trigger_sync(db: AsyncSession = Depends(get_db)) -> SyncTriggerResponse:
    provider_client = create_events_provider_client()
    try:
        result = await EventSyncService(db, provider_client).run_sync()
        return SyncTriggerResponse.from_result(result)
    finally:
        await provider_client.aclose()

from fastapi import APIRouter, Depends
from prometheus_client import REGISTRY, generate_latest
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.db.session import get_db
from app.services.metrics_service import refresh_database_gauges

router = APIRouter(tags=["metrics"])

PROMETHEUS_CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"


@router.get("/metrics")
async def metrics(db: AsyncSession = Depends(get_db)) -> Response:
    await refresh_database_gauges(db)
    return Response(
        content=generate_latest(REGISTRY),
        media_type=PROMETHEUS_CONTENT_TYPE,
    )

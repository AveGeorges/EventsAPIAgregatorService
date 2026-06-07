from fastapi import APIRouter

from app.api.v1.events import router as events_router
from app.api.v1.health import router as health_router
from app.api.v1.sync import router as sync_router
from app.api.v1.tickets import router as tickets_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(events_router)
api_router.include_router(tickets_router)
api_router.include_router(sync_router)

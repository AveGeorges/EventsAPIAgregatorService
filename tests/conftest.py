import os
import sys

if sys.platform == "win32":
    import asyncio

    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

os.environ.setdefault("EVENTS_PROVIDER_BASE_URL", "http://provider.test")
os.environ.setdefault("POSTGRES_HOST", "localhost")
os.environ.setdefault("SYNC_CRON_ENABLED", "false")
os.environ.setdefault("OUTBOX_WORKER_ENABLED", "false")
os.environ.setdefault("GLITCHTIP_DSN", "")
os.environ.setdefault("SENTRY_DSN", "")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings

test_engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    connect_args={"ssl": False},
)
TestSessionLocal = async_sessionmaker(
    bind=test_engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

import app.db.session as db_session

db_session.engine = test_engine
db_session.AsyncSessionLocal = TestSessionLocal

from app.db.session import get_db
from app.main import app


@pytest.fixture
async def _clean_database():
    try:
        async with test_engine.begin() as conn:
            await conn.execute(
                text(
                    "TRUNCATE TABLE idempotency, outbox, tickets, events, places, sync_state "
                    "RESTART IDENTITY CASCADE"
                )
            )
    except OSError as exc:
        pytest.skip(f"PostgreSQL unavailable: {exc}")
    except Exception as exc:
        pytest.skip(f"PostgreSQL unavailable: {exc.__class__.__name__}: {exc}")
    yield


@pytest.fixture
async def http_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def client(_clean_database):
    async def override_get_db():
        async with TestSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def db_session(_clean_database):
    async with TestSessionLocal() as session:
        yield session

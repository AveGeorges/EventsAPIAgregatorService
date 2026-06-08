from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Один фиксированный id «замка» для sync на весь сервис (все pod'ы используют одно число).
SYNC_ADVISORY_LOCK_ID = 834729105


async def try_acquire_sync_lock(session: AsyncSession) -> bool:
    """Пытается захватить lock. True — этот процесс может запускать sync."""
    result = await session.execute(
        text("SELECT pg_try_advisory_lock(:lock_id)"),
        {"lock_id": SYNC_ADVISORY_LOCK_ID},
    )
    return bool(result.scalar())


async def release_sync_lock(session: AsyncSession) -> None:
    """Освобождает lock после sync (вызывать в finally)."""
    await session.execute(
        text("SELECT pg_advisory_unlock(:lock_id)"),
        {"lock_id": SYNC_ADVISORY_LOCK_ID},
    )

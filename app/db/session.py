from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def configure_database(url: str) -> None:
    global _engine, _session_factory
    _engine = create_async_engine(url, echo=False)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False, autoflush=False)


async def dispose_database() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    if _session_factory is None:
        raise RuntimeError("Database is not configured (missing lifespan startup?)")
    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    if _session_factory is None:
        raise RuntimeError("Database is not configured (missing lifespan startup?)")
    return _session_factory


def get_engine() -> AsyncEngine | None:
    return _engine


async def create_all_tables() -> None:
    """Create tables (dev/tests). Migrations are preferred for production."""
    if _engine is None:
        raise RuntimeError("Database is not configured")
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

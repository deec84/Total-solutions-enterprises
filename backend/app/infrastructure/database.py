"""PostgreSQL async engine and transaction-scoped session factory."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.shared.config import get_settings

settings = get_settings()
engine = create_async_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    pool_recycle=1800,
)
session_factory = async_sessionmaker(engine, expire_on_commit=False, autoflush=False)


async def database_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session, session.begin():
        yield session

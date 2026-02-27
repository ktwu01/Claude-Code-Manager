"""Shared fixtures for backend tests."""
import asyncio
import os

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from backend.database import Base

# Import all models so Base.metadata knows about them for create_all
import backend.models.task  # noqa: F401
import backend.models.instance  # noqa: F401
import backend.models.project  # noqa: F401
import backend.models.log_entry  # noqa: F401
import backend.models.worktree  # noqa: F401

# Use in-memory SQLite for tests
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine):
    session_factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session


@pytest_asyncio.fixture
async def db_factory(db_engine):
    """Returns a session factory (contextmanager), matching the pattern used by services."""
    factory = async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)
    return factory

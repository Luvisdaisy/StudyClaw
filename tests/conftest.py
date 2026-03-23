"""Pytest fixtures for API integration tests."""
import asyncio
import os
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Set test environment before importing app
os.environ["TESTING"] = "1"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://studyclaw:secret@localhost:5432/studyclaw_test"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def db_engine():
    """Create a PostgreSQL engine for testing."""
    from database.models import Base

    test_db_url = "postgresql+asyncpg://studyclaw:secret@localhost:5432/studyclaw_test"
    engine = create_async_engine(
        test_db_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for a test."""
    async_session = async_sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_engine) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client for the FastAPI app."""
    from database.session import get_db
    from main import app

    # Override database dependency
    async def override_get_db():
        async_session = async_sessionmaker(
            db_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def sample_project(client: AsyncClient) -> dict:
    """Create a sample project via API."""
    response = await client.post(
        "/api/projects",
        json={"name": f"Test Project {uuid.uuid4()}", "description": "A test project"},
    )
    assert response.status_code == 200
    return response.json()

"""Pytest fixtures for E2E tests."""
import asyncio
import os
import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient

# E2E tests require a running server
# Set base URL via environment or use default
BASE_URL = os.environ.get("E2E_API_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an HTTP client for E2E tests."""
    async with AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        yield client


@pytest_asyncio.fixture
async def api_client(http_client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """Ensure API server is running and return client."""
    # Health check
    try:
        response = await http_client.get("/health")
        if response.status_code != 200:
            pytest.skip("API server not running or unhealthy")
    except Exception:
        pytest.skip("API server not accessible")

    await http_client.aclose()
    async with AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        yield client


@pytest.fixture
def unique_project_name() -> str:
    """Generate unique project name for tests."""
    return f"E2E Test Project {uuid.uuid4()}"

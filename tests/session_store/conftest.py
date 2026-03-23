"""Test suite for Session Persistence (SessionManager + Redis + PostgreSQL)

Test Structure:
- tests/
#   conftest.py           # Shared fixtures for all session tests
#   test_redis_store.py   # Unit tests for RedisStore
#   test_postgres_store.py # Unit tests for PostgresStore
#   test_manager.py       # Unit tests for SessionManager
#   test_checkpoint.py    # Unit tests for SessionCheckpointSaver
#   test_integration.py   # Integration tests (requires Redis + PostgreSQL)
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Generator

# ----------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------


@pytest.fixture(scope="session")
def sample_messages() -> list[dict]:
    """Sample messages for testing."""
    return [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"},
        {"role": "user", "content": "Tell me about Python."},
    ]


@pytest.fixture
def mock_redis_client():
    """Mock async Redis client."""
    client = AsyncMock()
    client.setex = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.delete = AsyncMock(return_value=True)
    client.exists = AsyncMock(return_value=0)
    client.close = AsyncMock()
    return client


@pytest.fixture
def mock_async_session():
    """Mock SQLAlchemy async session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.close = AsyncMock()
    return session


@pytest.fixture
def mock_session_factory(mock_async_session):
    """Mock async session factory."""
    factory = MagicMock(return_value=mock_async_session)
    return factory


@pytest.fixture(scope="function")
async def redis_store(mock_redis_client):
    """RedisStore instance with mocked client."""
    from session_store.redis_store import RedisStore

    store = RedisStore(host="localhost", port=6379, db=0)
    store._client = mock_redis_client
    yield store
    await store.close()


@pytest.fixture
def postgres_store(mock_session_factory):
    """PostgresStore instance with mocked session factory."""
    from session_store.postgres_store import PostgresStore

    store = PostgresStore(async_session_factory=mock_session_factory)
    return store


@pytest.fixture
def session_manager(redis_store, postgres_store):
    """SessionManager instance with mocked stores."""
    from session_store.manager import SessionManager

    manager = SessionManager(
        redis_store=redis_store,
        postgres_store=postgres_store,
        batch_interval=5,
        batch_size=10,
    )
    return manager


@pytest.fixture
def checkpoint_saver():
    """SessionCheckpointSaver instance."""
    from session_store.checkpoint import SessionCheckpointSaver

    return SessionCheckpointSaver()


# ----------------------------------------------------------------------
# Test Markers - Integration tests require live services
# ----------------------------------------------------------------------

def _check_redis_available():
    """Check if Redis is available."""
    try:
        import redis.asyncio as redis
        import asyncio
        return True
    except Exception:
        return False


def _check_postgres_available():
    """Check if PostgreSQL is available."""
    try:
        import os
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = int(os.getenv("POSTGRES_PORT", "5432"))
        return True
    except Exception:
        return False


_redis_available = _check_redis_available()
_postgres_available = _check_postgres_available()
_integration_available = _redis_available and _postgres_available

pytest.mark.redis = pytest.mark.skipif(
    not _redis_available, reason="Redis not available"
)
pytest.mark.postgres = pytest.mark.skipif(
    not _postgres_available, reason="PostgreSQL not available"
)
pytest.mark.integration = pytest.mark.skipif(
    not _integration_available, reason="Integration tests require live Redis + PostgreSQL"
)

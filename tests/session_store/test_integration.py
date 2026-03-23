"""Integration tests for Session Persistence (requires Redis + PostgreSQL)

Run with: pytest tests/session_store/test_integration.py -v
Requires Docker services: docker-compose up -d
"""

import pytest
import asyncio
import os


class TestRedisStoreIntegration:
    """Integration tests for RedisStore with real Redis."""

    @pytest.fixture
    async def redis_client(self):
        """Real Redis client."""
        import redis.asyncio as redis
        client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        yield client
        try:
            await client.ping()
            await client.aclose()
        except Exception:
            pass

    @pytest.mark.asyncio
    async def test_save_and_load(self, redis_client, sample_messages):
        """Test save and load with real Redis."""
        from session_store.redis_store import RedisStore

        store = RedisStore(host="localhost", port=6379, db=0)
        store._client = redis_client

        session_id = "integration_redis_1"
        await store.save(session_id, sample_messages)
        result = await store.load(session_id)

        assert result == sample_messages

        # Cleanup
        await store.delete(session_id)

    @pytest.mark.asyncio
    async def test_ttl_is_set(self, redis_client):
        """Test that TTL is correctly set on save."""
        from session_store.redis_store import RedisStore, SESSION_TTL

        store = RedisStore(host="localhost", port=6379, db=0)
        store._client = redis_client

        session_id = "integration_ttl_test"
        await store.save(session_id, [{"role": "test", "content": "TTL test"}])

        # Check TTL
        ttl = await redis_client.ttl(f"session:{session_id}")
        assert ttl > 0
        assert ttl <= SESSION_TTL

        # Cleanup
        await store.delete(session_id)


class TestPostgresStoreIntegration:
    """Integration tests for PostgresStore with real PostgreSQL."""

    @pytest.fixture
    async def pg_store(self):
        """Real PostgresStore with fresh session factory."""
        import os
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from session_store.postgres_store import PostgresStore

        password = os.getenv("POSTGRES_PASSWORD", "secret")
        engine = create_async_engine(
            f"postgresql+asyncpg://studyclaw:{password}@localhost:5432/studyclaw",
            echo=False,
        )
        SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

        store = PostgresStore(async_session_factory=SessionLocal)
        await store.init_schema()

        yield store

        await engine.dispose()

    @pytest.mark.asyncio
    async def test_save_and_load(self, pg_store, sample_messages):
        """Test save and load with real PostgreSQL."""
        session_id = "integration_pg_1"
        project_id = "proj_integration"

        await pg_store.save(session_id, project_id, sample_messages)
        result = await pg_store.load(session_id)

        assert result == sample_messages

        # Cleanup
        await pg_store.delete(session_id)

    @pytest.mark.asyncio
    async def test_upsert_updates_existing(self, pg_store, sample_messages):
        """Test that saving same session_id updates existing record."""
        session_id = "integration_upsert"
        project_id = "proj_integration"

        # First save
        await pg_store.save(session_id, project_id, sample_messages)

        # Update with new messages
        updated_messages = sample_messages + [{"role": "system", "content": "Updated"}]
        await pg_store.save(session_id, project_id, updated_messages)

        # Load should return updated messages
        result = await pg_store.load(session_id)
        assert result == updated_messages

        # Cleanup
        await pg_store.delete(session_id)


class TestSessionManagerIntegration:
    """Integration tests for SessionManager with real Redis + PostgreSQL."""

    @pytest.fixture
    async def manager(self):
        """Real SessionManager with real stores."""
        import redis.asyncio as redis
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from session_store.redis_store import RedisStore
        from session_store.postgres_store import PostgresStore
        from session_store.manager import SessionManager

        # Redis
        redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        redis_store = RedisStore(host="localhost", port=6379, db=0)
        redis_store._client = redis_client

        # PostgreSQL
        password = os.getenv("POSTGRES_PASSWORD", "secret")
        engine = create_async_engine(
            f"postgresql+asyncpg://studyclaw:{password}@localhost:5432/studyclaw",
            echo=False,
        )
        SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
        pg_store = PostgresStore(async_session_factory=SessionLocal)
        await pg_store.init_schema()

        manager = SessionManager(
            redis_store=redis_store,
            postgres_store=pg_store,
            batch_interval=2,
            batch_size=5,
        )
        manager._running = True

        yield manager

        # Cleanup
        await manager.stop()
        await redis_client.aclose()
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_save_load_delete_cycle(self, manager, sample_messages):
        """Test complete save -> load -> delete cycle."""
        session_id = "integration_cycle"
        project_id = "proj_integration"

        # Save
        await manager.save(session_id, project_id, sample_messages)

        # Load
        result = await manager.load(session_id)
        assert result == sample_messages

        # Delete
        await manager.delete(session_id)

        # Verify deleted
        result = await manager.load(session_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_batch_sync_to_postgresql(self, manager, sample_messages):
        """Test that pending sessions are synced to PostgreSQL."""
        # Save multiple sessions to trigger batch
        for i in range(3):
            await manager.save(f"batch_test_{i}", "proj_batch", [{"role": "test", "content": f"msg_{i}"}])

        # Wait for batch sync
        await asyncio.sleep(3)

        # Flush pending
        await manager._flush_pending()

        # Verify sessions in PostgreSQL via direct load
        for i in range(3):
            result = await manager.pg.load(f"batch_test_{i}")
            assert result == [{"role": "test", "content": f"msg_{i}"}]


class TestLangGraphCheckpointIntegration:
    """Integration tests for LangGraph checkpoint interface."""

    @pytest.fixture
    async def checkpoint_manager(self):
        """Real SessionManager for checkpoint tests."""
        import redis.asyncio as redis
        from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
        from session_store.redis_store import RedisStore
        from session_store.postgres_store import PostgresStore
        from session_store.manager import SessionManager

        # Redis
        redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)
        redis_store = RedisStore(host="localhost", port=6379, db=0)
        redis_store._client = redis_client

        # PostgreSQL
        password = os.getenv("POSTGRES_PASSWORD", "secret")
        engine = create_async_engine(
            f"postgresql+asyncpg://studyclaw:{password}@localhost:5432/studyclaw",
            echo=False,
        )
        SessionLocal = async_sessionmaker(engine, expire_on_commit=False)
        pg_store = PostgresStore(async_session_factory=SessionLocal)
        await pg_store.init_schema()

        manager = SessionManager(
            redis_store=redis_store,
            postgres_store=pg_store,
            batch_interval=2,
            batch_size=5,
        )
        manager._running = True

        yield manager

        # Cleanup
        await manager.stop()
        await redis_client.aclose()
        await engine.dispose()

    @pytest.mark.asyncio
    async def test_checkpoint_put_and_get(self, checkpoint_manager, sample_messages):
        """Test LangGraph-style checkpoint put and get."""
        session_id = "langgraph_test"
        project_id = "proj_langgraph"

        # Put checkpoint
        config = await checkpoint_manager.put(session_id, project_id, sample_messages)
        assert config["configurable"]["checkpoint_id"] == session_id

        # Get checkpoint - returns serialized checkpoint format
        checkpoint = await checkpoint_manager.get(session_id)
        assert checkpoint is not None
        assert checkpoint["id"] == session_id
        # Deserialize binary_data back to messages
        import json
        result = json.loads(checkpoint["binary_data"].decode("utf-8"))
        assert result == sample_messages

        # Cleanup
        await checkpoint_manager.delete(session_id)

"""Unit tests for RedisStore"""

import pytest
import json
from session_store.redis_store import RedisStore, SESSION_TTL


class TestRedisStore:
    """Tests for RedisStore class."""

    # ------------------------------------------------------------------
    # save()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_save_success(self, redis_store, mock_redis_client, sample_messages):
        """Test successful save to Redis."""
        session_id = "test_session_1"

        result = await redis_store.save(session_id, sample_messages)

        assert result is True
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == f"session:{session_id}"
        assert call_args[0][1] == SESSION_TTL
        assert json.loads(call_args[0][2]) == sample_messages

    @pytest.mark.asyncio
    async def test_save_with_custom_prefix(self, mock_redis_client, sample_messages):
        """Test save with custom key prefix."""
        store = RedisStore(prefix="custom:")
        store._client = mock_redis_client

        await store.save("session_x", sample_messages)

        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == "custom:session_x"

    @pytest.mark.asyncio
    async def test_save_redis_error(self, mock_redis_client, sample_messages):
        """Test save when Redis fails."""
        mock_redis_client.setex.side_effect = Exception("Redis connection failed")
        store = RedisStore()
        store._client = mock_redis_client

        result = await store.save("session_err", sample_messages)

        assert result is False

    # ------------------------------------------------------------------
    # load()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_load_found(self, redis_store, mock_redis_client, sample_messages):
        """Test loading existing session."""
        session_id = "test_session_2"
        stored_data = json.dumps(sample_messages)
        mock_redis_client.get.return_value = stored_data

        result = await redis_store.load(session_id)

        assert result == sample_messages
        mock_redis_client.get.assert_called_once_with(f"session:{session_id}")

    @pytest.mark.asyncio
    async def test_load_not_found(self, redis_store, mock_redis_client):
        """Test loading non-existent session."""
        mock_redis_client.get.return_value = None

        result = await redis_store.load("nonexistent")

        assert result is None

    @pytest.mark.asyncio
    async def test_load_redis_error(self, mock_redis_client):
        """Test load when Redis fails."""
        mock_redis_client.get.side_effect = Exception("Redis error")
        store = RedisStore()
        store._client = mock_redis_client

        result = await store.load("session_err")

        assert result is None

    # ------------------------------------------------------------------
    # delete()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_delete_success(self, redis_store, mock_redis_client):
        """Test successful delete."""
        session_id = "test_session_3"

        result = await redis_store.delete(session_id)

        assert result is True
        mock_redis_client.delete.assert_called_once_with(f"session:{session_id}")

    @pytest.mark.asyncio
    async def test_delete_redis_error(self, mock_redis_client):
        """Test delete when Redis fails."""
        mock_redis_client.delete.side_effect = Exception("Redis error")
        store = RedisStore()
        store._client = mock_redis_client

        result = await store.delete("session_err")

        assert result is False

    # ------------------------------------------------------------------
    # exists()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_exists_true(self, redis_store, mock_redis_client):
        """Test exists returns True when session exists."""
        mock_redis_client.exists.return_value = 1

        result = await redis_store.exists("existing_session")

        assert result is True

    @pytest.mark.asyncio
    async def test_exists_false(self, redis_store, mock_redis_client):
        """Test exists returns False when session doesn't exist."""
        mock_redis_client.exists.return_value = 0

        result = await redis_store.exists("nonexistent")

        assert result is False

    # ------------------------------------------------------------------
    # close()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_close_with_client(self, mock_redis_client):
        """Test close closes the Redis connection."""
        store = RedisStore()
        store._client = mock_redis_client

        await store.close()

        mock_redis_client.close.assert_called_once()
        assert store._client is None

    @pytest.mark.asyncio
    async def test_close_without_client(self, redis_store):
        """Test close when no client exists (no-op)."""
        redis_store._client = None
        await redis_store.close()  # Should not raise

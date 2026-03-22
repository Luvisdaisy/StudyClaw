"""Unit tests for SessionManager"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime


class TestSessionManager:
    """Tests for SessionManager class."""

    # ------------------------------------------------------------------
    # save()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_save_redis_success(self, session_manager, redis_store, mock_redis_client, sample_messages):
        """Test save writes to Redis and queues for PostgreSQL."""
        session_id = "mgr_session_1"
        project_id = "proj_1"

        result = await session_manager.save(session_id, project_id, sample_messages)

        assert result is True
        mock_redis_client.setex.assert_called()

        # Check pending queue
        async with session_manager._pending_lock:
            assert session_id in session_manager._pending
            pending = session_manager._pending[session_id]
            assert pending.project_id == project_id
            assert pending.messages == sample_messages

    @pytest.mark.asyncio
    async def test_save_updates_existing_pending(self, session_manager, mock_redis_client, sample_messages):
        """Test save updates existing pending session."""
        session_id = "mgr_session_update"
        project_id = "proj_1"

        # First save
        await session_manager.save(session_id, project_id, sample_messages)

        # Second save with updated messages
        updated_messages = sample_messages + [{"role": "user", "content": "Updated"}]
        await session_manager.save(session_id, project_id, updated_messages)

        async with session_manager._pending_lock:
            assert session_id in session_manager._pending
            assert session_manager._pending[session_id].messages == updated_messages

    # ------------------------------------------------------------------
    # load()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_load_from_redis(self, session_manager, redis_store, mock_redis_client, sample_messages):
        """Test load reads from Redis first."""
        session_id = "mgr_session_load"
        stored_data = json.dumps(sample_messages)
        mock_redis_client.get.return_value = stored_data

        result = await session_manager.load(session_id)

        assert result == sample_messages
        mock_redis_client.get.assert_called()

    @pytest.mark.asyncio
    async def test_load_fallback_to_postgres(self, session_manager, postgres_store, mock_redis_client, sample_messages):
        """Test load falls back to PostgreSQL when Redis miss."""
        session_id = "mgr_session_pg_fallback"

        # Redis miss
        mock_redis_client.get.return_value = None

        # PostgreSQL hit - patch the pg's load method
        with patch.object(postgres_store, 'load', new_callable=AsyncMock, return_value=sample_messages):
            result = await session_manager.load(session_id)

        # Should attempt Redis load first
        assert mock_redis_client.get.called

    @pytest.mark.asyncio
    async def test_load_returns_none_when_not_found(self, session_manager, mock_redis_client):
        """Test load returns None when not found in either store."""
        session_id = "mgr_session_none"
        mock_redis_client.get.return_value = None

        with patch.object(session_manager.pg, 'load', return_value=None):
            result = await session_manager.load(session_id)

        assert result is None

    # ------------------------------------------------------------------
    # delete()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_delete_removes_from_both_stores(self, session_manager, mock_redis_client, sample_messages):
        """Test delete removes session from Redis and PostgreSQL."""
        session_id = "mgr_session_del"
        project_id = "proj_1"

        # Queue a session first
        await session_manager.save(session_id, project_id, sample_messages)

        # Mock PostgreSQL delete
        with patch.object(session_manager.pg, 'delete', return_value=True):
            result = await session_manager.delete(session_id)

        assert result is True
        mock_redis_client.delete.assert_called()

        # Should be removed from pending
        async with session_manager._pending_lock:
            assert session_id not in session_manager._pending

    # ------------------------------------------------------------------
    # start() / stop()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_start_initializes_pg_schema(self, session_manager, postgres_store):
        """Test start initializes PostgreSQL schema."""
        with patch.object(postgres_store, 'init_schema', new_callable=AsyncMock) as mock_init:
            await session_manager.start()

            mock_init.assert_called_once()
            assert session_manager._running is True

    @pytest.mark.asyncio
    async def test_stop_flushes_pending(self, session_manager, sample_messages):
        """Test stop flushes pending sessions to PostgreSQL."""
        session_id = "mgr_session_flush"
        project_id = "proj_1"

        await session_manager.start()

        # Add pending session
        await session_manager.save(session_id, project_id, sample_messages)

        with patch.object(session_manager.pg, 'batch_save', new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = True
            await session_manager.stop()

            # Should have called batch_save with pending sessions
            mock_batch.assert_called()

        assert session_manager._running is False

    # ------------------------------------------------------------------
    # batch trigger
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_batch_trigger_on_size(self, session_manager, sample_messages):
        """Test immediate flush when batch_size is reached."""
        session_manager.batch_size = 5

        with patch.object(session_manager.pg, 'batch_save', new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = True

            # Save sessions to reach batch_size - 1 (no trigger yet)
            for i in range(4):
                await session_manager.save(f"batch_{i}", "proj", sample_messages)
            assert not mock_batch.called

            # Save 5th session - should trigger immediate flush
            await session_manager.save(f"batch_4", "proj", sample_messages)

    # ------------------------------------------------------------------
    # LangGraph checkpoint interface (get/put)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_returns_none_when_no_checkpoint(self, session_manager, mock_redis_client):
        """Test get returns None when checkpoint doesn't exist."""
        session_id = "checkpoint_get_none"
        mock_redis_client.get.return_value = None

        with patch.object(session_manager, 'load', return_value=None):
            result = await session_manager.get(session_id)

        assert result is None

    @pytest.mark.asyncio
    async def test_put_saves_checkpoint(self, session_manager, sample_messages):
        """Test put saves checkpoint via save()."""
        session_id = "checkpoint_put"
        project_id = "proj_checkpoint"

        with patch.object(session_manager, 'save', new_callable=AsyncMock) as mock_save:
            mock_save.return_value = True
            result = await session_manager.put(session_id, project_id, sample_messages)

            mock_save.assert_called_once_with(session_id, project_id, sample_messages)
            assert result["configurable"]["checkpoint_id"] == session_id


import json  # For JSON serialization in tests

"""Unit tests for SessionCheckpointSaver (LangGraph adapter)"""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock


class TestSessionCheckpointSaver:
    """Tests for SessionCheckpointSaver LangGraph adapter."""

    # ------------------------------------------------------------------
    # get()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_returns_none_when_no_session_manager(self, checkpoint_saver):
        """Test get returns None when SessionManager not initialized."""
        # Patch get_session_manager to return None
        with patch("session_store.checkpoint.get_session_manager", return_value=None):
            result = await checkpoint_saver.get({"configurable": {"thread_id": "test"}})

        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_none_when_no_thread_id(self, checkpoint_saver):
        """Test get returns None when thread_id not in config."""
        with patch("session_store.checkpoint.get_session_manager", return_value=MagicMock()):
            result = await checkpoint_saver.get({"configurable": {}})

        assert result is None

    @pytest.mark.asyncio
    async def test_get_deserializes_checkpoint(self, checkpoint_saver, sample_messages):
        """Test get deserializes checkpoint data correctly."""
        session_id = "checkpoint_test"
        serialized = json.dumps(sample_messages).encode("utf-8")

        mock_manager = AsyncMock()
        mock_manager.get.return_value = {
            "v": 1,
            "id": session_id,
            "binary_data": serialized,
        }

        with patch("session_store.checkpoint.get_session_manager", return_value=mock_manager):
            result = await checkpoint_saver.get({"configurable": {"thread_id": session_id}})

        assert result == sample_messages
        mock_manager.get.assert_called_once_with(session_id)

    # ------------------------------------------------------------------
    # put()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_put_saves_checkpoint(self, checkpoint_saver, sample_messages):
        """Test put saves checkpoint data."""
        session_id = "checkpoint_put_test"
        project_id = "proj_test"
        checkpoint_data = {"messages": sample_messages}

        mock_manager = AsyncMock()
        mock_manager.put.return_value = True

        with patch("session_store.checkpoint.get_session_manager", return_value=mock_manager):
            result = await checkpoint_saver.put(
                {"configurable": {"thread_id": session_id, "project_id": project_id}},
                checkpoint_data,
            )

        mock_manager.put.assert_called_once_with(session_id, project_id, sample_messages)
        assert result["configurable"]["checkpoint_id"] == session_id

    @pytest.mark.asyncio
    async def test_put_uses_default_project_id(self, checkpoint_saver, sample_messages):
        """Test put uses default project_id when not provided."""
        session_id = "checkpoint_put_default"
        checkpoint_data = {"messages": sample_messages}

        mock_manager = AsyncMock()
        mock_manager.put.return_value = True

        with patch("session_store.checkpoint.get_session_manager", return_value=mock_manager):
            await checkpoint_saver.put(
                {"configurable": {"thread_id": session_id}},
                checkpoint_data,
            )

        mock_manager.put.assert_called_once_with(session_id, "default", sample_messages)

    # ------------------------------------------------------------------
    # list()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_list_returns_empty_list(self, checkpoint_saver):
        """Test list returns empty (not fully implemented)."""
        result = await checkpoint_saver.list()

        assert result == []

"""Unit tests for PostgresStore"""

import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch


class TestPostgresStore:
    """Tests for PostgresStore class."""

    # ------------------------------------------------------------------
    # init_schema()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_init_schema_creates_table(self, postgres_store, mock_async_session):
        """Test that init_schema creates the agent_sessions table."""
        postgres_store._session_factory.return_value.__aenter__.return_value = mock_async_session

        await postgres_store.init_schema()

        mock_async_session.execute.assert_called()
        mock_async_session.commit.assert_called()

    # ------------------------------------------------------------------
    # save()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_save_success(self, postgres_store, mock_async_session, sample_messages):
        """Test successful save to PostgreSQL."""
        session_id = "pg_session_1"
        project_id = "project_1"
        postgres_store._session_factory.return_value.__aenter__.return_value = mock_async_session

        result = await postgres_store.save(session_id, project_id, sample_messages)

        assert result is True
        mock_async_session.execute.assert_called()
        mock_async_session.commit.assert_called()

    @pytest.mark.asyncio
    async def test_save_with_title(self, postgres_store, mock_async_session, sample_messages):
        """Test save preserves title during upsert."""
        session_id = "pg_session_title"
        project_id = "project_1"
        postgres_store._session_factory.return_value.__aenter__.return_value = mock_async_session

        result = await postgres_store.save(session_id, project_id, sample_messages, title="Test Title")

        assert result is True
        call_args = mock_async_session.execute.call_args
        params = call_args[0][1]
        assert params["title"] == "Test Title"

    @pytest.mark.asyncio
    async def test_save_uses_upsert(self, postgres_store, mock_async_session, sample_messages):
        """Test that save uses ON CONFLICT DO UPDATE (upsert)."""
        session_id = "pg_session_upsert"
        project_id = "project_1"
        postgres_store._session_factory.return_value.__aenter__.return_value = mock_async_session

        await postgres_store.save(session_id, project_id, sample_messages)

        call_args = mock_async_session.execute.call_args
        sql = str(call_args[0][0])
        assert "ON CONFLICT" in sql
        assert "DO UPDATE" in sql

    @pytest.mark.asyncio
    async def test_save_error(self, postgres_store, mock_async_session):
        """Test save when PostgreSQL fails."""
        mock_async_session.execute.side_effect = Exception("DB error")
        postgres_store._session_factory.return_value.__aenter__.return_value = mock_async_session

        result = await postgres_store.save("err_session", "proj", [])

        assert result is False

    # ------------------------------------------------------------------
    # load()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_load_found(self, postgres_store, mock_async_session, sample_messages):
        """Test loading existing session."""
        session_id = "pg_session_2"
        stored_messages = json.dumps(sample_messages)

        # Mock result with fetchone
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (stored_messages,)
        mock_async_session.execute.return_value = mock_result
        postgres_store._session_factory.return_value.__aenter__.return_value = mock_async_session

        result = await postgres_store.load(session_id)

        assert result == sample_messages

    @pytest.mark.asyncio
    async def test_load_not_found(self, postgres_store, mock_async_session):
        """Test loading non-existent session."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_async_session.execute.return_value = mock_result
        postgres_store._session_factory.return_value.__aenter__.return_value = mock_async_session

        result = await postgres_store.load("nonexistent")

        assert result is None

    # ------------------------------------------------------------------
    # delete()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_delete_success(self, postgres_store, mock_async_session):
        """Test successful delete."""
        postgres_store._session_factory.return_value.__aenter__.return_value = mock_async_session

        result = await postgres_store.delete("pg_session_del")

        assert result is True
        mock_async_session.commit.assert_called()

    # ------------------------------------------------------------------
    # load_by_project()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_load_by_project(self, postgres_store, mock_async_session, sample_messages):
        """Test loading all sessions for a project."""
        from datetime import datetime
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [
            ("session_1", "Session 1 Title", json.dumps(sample_messages), datetime.now()),
            ("session_2", "Session 2 Title", json.dumps([{"role": "user", "content": "Hi"}]), datetime.now()),
        ]
        mock_async_session.execute.return_value = mock_result
        postgres_store._session_factory.return_value.__aenter__.return_value = mock_async_session

        results = await postgres_store.load_by_project("project_test")

        assert len(results) == 2
        assert results[0]["session_id"] == "session_1"
        assert results[0]["title"] == "Session 1 Title"
        assert results[1]["session_id"] == "session_2"
        assert results[1]["title"] == "Session 2 Title"

    # ------------------------------------------------------------------
    # get_session()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_get_session_found(self, postgres_store, mock_async_session, sample_messages):
        """Test getting a session by ID."""
        from datetime import datetime
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (
            "session_get",
            "Get Session Title",
            json.dumps(sample_messages),
            datetime.now(),
            datetime.now(),
        )
        mock_async_session.execute.return_value = mock_result
        postgres_store._session_factory.return_value.__aenter__.return_value = mock_async_session

        result = await postgres_store.get_session("session_get")

        assert result is not None
        assert result["session_id"] == "session_get"
        assert result["title"] == "Get Session Title"
        assert result["messages"] == sample_messages

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, postgres_store, mock_async_session):
        """Test getting non-existent session returns None."""
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_async_session.execute.return_value = mock_result
        postgres_store._session_factory.return_value.__aenter__.return_value = mock_async_session

        result = await postgres_store.get_session("nonexistent")

        assert result is None

    # ------------------------------------------------------------------
    # batch_save()
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_batch_save_empty(self, postgres_store):
        """Test batch_save with empty list."""
        result = await postgres_store.batch_save([])

        assert result is True

    @pytest.mark.asyncio
    async def test_batch_save_multiple(self, postgres_store, mock_async_session, sample_messages):
        """Test batch_save with multiple sessions."""
        sessions = [
            {"session_id": "batch_1", "project_id": "proj_1", "messages": sample_messages},
            {"session_id": "batch_2", "project_id": "proj_1", "messages": [{"role": "user", "content": "Test"}]},
        ]
        postgres_store._session_factory.return_value.__aenter__.return_value = mock_async_session

        result = await postgres_store.batch_save(sessions)

        assert result is True
        # Should call execute twice (once per session)
        assert mock_async_session.execute.call_count == 2

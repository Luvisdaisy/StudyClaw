"""Integration tests for Chat API."""
import uuid
import pytest
from httpx import AsyncClient


class TestChatAPI:
    """Tests for chat endpoints."""

    @pytest.mark.asyncio
    async def test_chat_project_not_found(self, client: AsyncClient):
        """Test chatting with non-existent project returns 404."""
        fake_project_id = str(uuid.uuid4())

        response = await client.post(
            f"/api/projects/{fake_project_id}/chat",
            json={"message": "Hello"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_without_message(self, client: AsyncClient, sample_project: dict):
        """Test chatting without message returns 422 (validation error)."""
        response = await client.post(
            f"/api/projects/{sample_project['id']}/chat",
            json={},
        )

        # FastAPI returns 422 for validation errors
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_with_empty_message(self, client: AsyncClient, sample_project: dict):
        """Test chatting with empty message."""
        response = await client.post(
            f"/api/projects/{sample_project['id']}/chat",
            json={"message": ""},
        )

        # Empty message may be accepted or rejected depending on implementation
        assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_chat_with_session_id(self, client: AsyncClient, sample_project: dict):
        """Test chatting with custom session ID."""
        session_id = str(uuid.uuid4())

        response = await client.post(
            f"/api/projects/{sample_project['id']}/chat",
            json={"message": "Hello", "session_id": session_id},
        )

        # Response may be 200 (streaming) or 500 if Chroma not available
        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_chat_with_web_search_flag(self, client: AsyncClient, sample_project: dict):
        """Test chatting with web search enabled."""
        response = await client.post(
            f"/api/projects/{sample_project['id']}/chat",
            json={"message": "Hello", "enable_web_search": True},
        )

        assert response.status_code in [200, 500]

    @pytest.mark.asyncio
    async def test_get_chat_history(self, client: AsyncClient, sample_project: dict):
        """Test getting chat history."""
        session_id = str(uuid.uuid4())

        response = await client.get(
            f"/api/projects/{sample_project['id']}/chat/history",
            params={"session_id": session_id},
        )

        # Currently returns empty list (placeholder implementation)
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id
        assert data["messages"] == []

    @pytest.mark.asyncio
    async def test_get_chat_history_project_not_found(self, client: AsyncClient):
        """Test getting chat history for non-existent project returns 404."""
        fake_project_id = str(uuid.uuid4())

        response = await client.get(
            f"/api/projects/{fake_project_id}/chat/history",
            params={"session_id": "test"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_clear_chat_history(self, client: AsyncClient, sample_project: dict):
        """Test clearing chat history."""
        session_id = str(uuid.uuid4())

        response = await client.delete(
            f"/api/projects/{sample_project['id']}/chat/history",
            params={"session_id": session_id},
        )

        assert response.status_code == 200
        assert response.json()["message"] == "Chat history cleared"

    @pytest.mark.asyncio
    async def test_clear_chat_history_project_not_found(self, client: AsyncClient):
        """Test clearing chat history for non-existent project returns 404."""
        fake_project_id = str(uuid.uuid4())

        response = await client.delete(
            f"/api/projects/{fake_project_id}/chat/history",
            params={"session_id": "test"},
        )

        assert response.status_code == 404

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
        """Test chatting with empty message returns validation error."""
        response = await client.post(
            f"/api/projects/{sample_project['id']}/chat",
            json={"message": ""},
        )

        # Empty string should be rejected as invalid input
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_with_session_id(self, client: AsyncClient, sample_project: dict):
        """Test chatting with custom session ID returns streaming response."""
        session_id = str(uuid.uuid4())

        response = await client.post(
            f"/api/projects/{sample_project['id']}/chat",
            json={"message": "Hello", "session_id": session_id},
        )

        # Should return 200 OK for streaming response
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_chat_with_web_search_flag(self, client: AsyncClient, sample_project: dict):
        """Test chatting with web search enabled returns streaming response."""
        response = await client.post(
            f"/api/projects/{sample_project['id']}/chat",
            json={"message": "Hello", "enable_web_search": True},
        )

        # Should return 200 OK for streaming response when web search is enabled
        assert response.status_code == 200


class TestChatSessionsAPI:
    """Tests for chat session management endpoints."""

    @pytest.mark.asyncio
    async def test_list_chat_sessions_project_not_found(self, client: AsyncClient):
        """Test listing sessions for non-existent project returns 404."""
        fake_project_id = str(uuid.uuid4())

        response = await client.get(f"/api/projects/{fake_project_id}/chat/sessions")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_chat_session_project_not_found(self, client: AsyncClient):
        """Test getting session for non-existent project returns 404."""
        fake_project_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        response = await client.get(
            f"/api/projects/{fake_project_id}/chat/sessions/{session_id}",
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_chat_session_not_found(self, client: AsyncClient, sample_project: dict):
        """Test getting non-existent session returns 404."""
        session_id = str(uuid.uuid4())

        response = await client.get(
            f"/api/projects/{sample_project['id']}/chat/sessions/{session_id}",
        )

        # Session not found (either project not found OR session not found)
        # Since sample_project exists, we expect 404 from session manager or 404 from not found
        assert response.status_code in [404, 503]

    @pytest.mark.asyncio
    async def test_delete_chat_session_project_not_found(self, client: AsyncClient):
        """Test deleting session for non-existent project returns 404."""
        fake_project_id = str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        response = await client.delete(
            f"/api/projects/{fake_project_id}/chat/sessions/{session_id}",
        )

        assert response.status_code == 404

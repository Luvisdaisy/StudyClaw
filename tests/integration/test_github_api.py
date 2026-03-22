"""Integration tests for GitHub API."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient


class TestGitHubAPI:
    """Tests for GitHub integration endpoints."""

    @pytest.mark.asyncio
    async def test_connect_github_invalid_token(self, client: AsyncClient, sample_project: dict):
        """Test connecting GitHub with invalid token returns 400."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_client.__aenter__.return_value.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            response = await client.post(
                f"/api/projects/{sample_project['id']}/github/connect",
                json={"token": "invalid_token"},
            )

            assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_connect_github_valid_token(self, client: AsyncClient, sample_project: dict):
        """Test connecting GitHub with valid token."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "login": "testuser",
                "name": "Test User",
                "avatar_url": "https://github.com/avatars/testuser.png",
            }
            mock_client.__aenter__.return_value.get.return_value = mock_response
            mock_client_class.return_value = mock_client

            response = await client.post(
                f"/api/projects/{sample_project['id']}/github/connect",
                json={"token": "valid_token"},
            )

            assert response.status_code == 200
            data = response.json()
            assert data["login"] == "testuser"

    @pytest.mark.asyncio
    async def test_disconnect_github(self, client: AsyncClient, sample_project: dict):
        """Test disconnecting GitHub."""
        response = await client.post(
            f"/api/projects/{sample_project['id']}/github/disconnect",
        )

        assert response.status_code == 200
        assert "disconnected" in response.json()["message"]

    @pytest.mark.asyncio
    async def test_list_github_repos_not_connected(self, client: AsyncClient, sample_project: dict):
        """Test listing repos when GitHub not connected returns 400."""
        response = await client.get(
            f"/api/projects/{sample_project['id']}/github/repos",
        )

        assert response.status_code == 400
        assert "not connected" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_get_sync_status_idle(self, client: AsyncClient, sample_project: dict):
        """Test getting sync status when not synced."""
        response = await client.get(
            f"/api/projects/{sample_project['id']}/github/sync/status",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "idle"

    @pytest.mark.asyncio
    async def test_trigger_sync_not_connected(self, client: AsyncClient, sample_project: dict):
        """Test triggering sync when not connected returns 400."""
        response = await client.post(
            f"/api/projects/{sample_project['id']}/github/sync",
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_get_github_user_not_connected(self, client: AsyncClient, sample_project: dict):
        """Test getting GitHub user when not connected returns None."""
        response = await client.get(
            f"/api/projects/{sample_project['id']}/github/user",
        )

        # Returns None (not connected)
        assert response.status_code == 200
        assert response.json() is None

    @pytest.mark.asyncio
    async def test_select_github_repo_not_connected(self, client: AsyncClient, sample_project: dict):
        """Test selecting repo when not connected returns 400."""
        response = await client.patch(
            f"/api/projects/{sample_project['id']}/github/repo",
            json={"repo_full_name": "user/repo", "default_branch": "main"},
        )

        assert response.status_code == 400

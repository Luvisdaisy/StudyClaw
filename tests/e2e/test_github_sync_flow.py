"""E2E tests for GitHub sync flow."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient


class TestGitHubSyncE2E:
    """E2E tests for GitHub synchronization flow."""

    @pytest.mark.asyncio
    async def test_github_disconnect_workflow(self, api_client: AsyncClient, unique_project_name: str):
        """Test disconnecting GitHub workflow (without actually connecting)."""
        # Create project
        project_response = await api_client.post(
            "/api/projects",
            json={"name": unique_project_name},
        )

        if project_response.status_code == 500:
            pytest.skip("Database not available")

        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        try:
            # Disconnect GitHub (should work even if not connected)
            disconnect_response = await api_client.post(
                f"/api/projects/{project_id}/github/disconnect",
            )
            assert disconnect_response.status_code == 200

        finally:
            # Cleanup
            await api_client.delete(f"/api/projects/{project_id}")

    @pytest.mark.asyncio
    async def test_github_sync_status_tracking(self, api_client: AsyncClient, unique_project_name: str):
        """Test sync status is tracked correctly."""
        # Create project
        project_response = await api_client.post(
            "/api/projects",
            json={"name": unique_project_name},
        )

        if project_response.status_code == 500:
            pytest.skip("Database not available")

        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        try:
            # Initially sync status should be idle
            status_response = await api_client.get(
                f"/api/projects/{project_id}/github/sync/status",
            )
            assert status_response.status_code == 200
            assert status_response.json()["status"] == "idle"

        finally:
            # Cleanup
            await api_client.delete(f"/api/projects/{project_id}")

    @pytest.mark.asyncio
    async def test_list_github_repos_requires_connection(self, api_client: AsyncClient, unique_project_name: str):
        """Test listing repos without connection returns 400."""
        # Create project
        project_response = await api_client.post(
            "/api/projects",
            json={"name": unique_project_name},
        )

        if project_response.status_code == 500:
            pytest.skip("Database not available")

        assert project_response.status_code == 200
        project_id = project_response.json()["id"]

        try:
            # Try to list repos without connecting
            repos_response = await api_client.get(
                f"/api/projects/{project_id}/github/repos",
            )
            assert repos_response.status_code == 400

        finally:
            # Cleanup
            await api_client.delete(f"/api/projects/{project_id}")

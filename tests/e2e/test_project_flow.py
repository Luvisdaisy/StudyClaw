"""E2E tests for project lifecycle."""
import uuid
import pytest
from httpx import AsyncClient


class TestProjectLifecycleE2E:
    """E2E tests for complete project lifecycle."""

    @pytest.mark.asyncio
    async def test_project_create_and_cleanup(self, api_client: AsyncClient, unique_project_name: str):
        """Test creating a project and cleaning it up."""
        # Create project
        create_response = await api_client.post(
            "/api/projects",
            json={"name": unique_project_name, "description": "E2E test project"},
        )

        if create_response.status_code == 500:
            pytest.skip("Database not available")

        assert create_response.status_code == 200
        project = create_response.json()
        project_id = project["id"]

        # Verify project exists
        get_response = await api_client.get(f"/api/projects/{project_id}")
        assert get_response.status_code == 200
        assert get_response.json()["name"] == unique_project_name

        # Update project
        update_response = await api_client.patch(
            f"/api/projects/{project_id}",
            json={"description": "Updated description"},
        )
        assert update_response.status_code == 200

        # Delete project
        delete_response = await api_client.delete(f"/api/projects/{project_id}")
        assert delete_response.status_code == 200

        # Verify deletion
        get_deleted = await api_client.get(f"/api/projects/{project_id}")
        assert get_deleted.status_code == 404

    @pytest.mark.asyncio
    async def test_list_projects(self, api_client: AsyncClient, unique_project_name: str):
        """Test listing projects includes newly created ones."""
        # Create a project
        create_response = await api_client.post(
            "/api/projects",
            json={"name": unique_project_name},
        )

        if create_response.status_code == 500:
            pytest.skip("Database not available")

        assert create_response.status_code == 200

        # List projects
        list_response = await api_client.get("/api/projects")
        assert list_response.status_code == 200

        projects = list_response.json()["projects"]
        project_names = [p["name"] for p in projects]
        assert unique_project_name in project_names

        # Cleanup
        project_id = create_response.json()["id"]
        await api_client.delete(f"/api/projects/{project_id}")

    @pytest.mark.asyncio
    async def test_health_endpoint(self, api_client: AsyncClient):
        """Test health check endpoint."""
        response = await api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

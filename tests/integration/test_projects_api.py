"""Integration tests for Projects API."""
import uuid
import pytest
from httpx import AsyncClient


class TestProjectsAPI:
    """Tests for /api/projects endpoints."""

    @pytest.mark.asyncio
    async def test_create_project_success(self, client: AsyncClient):
        """Test creating a project successfully."""
        response = await client.post(
            "/api/projects",
            json={"name": f"New Project {uuid.uuid4()}", "description": "Test description"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"].startswith("New Project")
        assert data["description"] == "Test description"

    @pytest.mark.asyncio
    async def test_create_project_duplicate_name(self, client: AsyncClient):
        """Test creating project with duplicate name returns 400."""
        name = f"Duplicate Test {uuid.uuid4()}"

        # Create first project
        response1 = await client.post(
            "/api/projects",
            json={"name": name},
        )
        assert response1.status_code == 200

        # Try to create second project with same name
        response2 = await client.post(
            "/api/projects",
            json={"name": name},
        )
        assert response2.status_code == 400
        assert "already exists" in response2.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_project_without_description(self, client: AsyncClient):
        """Test creating project without description."""
        response = await client.post(
            "/api/projects",
            json={"name": f"No Description {uuid.uuid4()}"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] is None

    @pytest.mark.asyncio
    async def test_list_projects_empty(self, client: AsyncClient):
        """Test listing projects when none exist."""
        response = await client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert "projects" in data
        assert isinstance(data["projects"], list)

    @pytest.mark.asyncio
    async def test_list_projects_with_data(self, client: AsyncClient):
        """Test listing projects returns created projects."""
        # Create a project
        await client.post(
            "/api/projects",
            json={"name": f"List Test {uuid.uuid4()}"},
        )

        response = await client.get("/api/projects")

        assert response.status_code == 200
        data = response.json()
        assert len(data["projects"]) >= 1

    @pytest.mark.asyncio
    async def test_get_project_success(self, client: AsyncClient, sample_project: dict):
        """Test getting a project by ID."""
        response = await client.get(f"/api/projects/{sample_project['id']}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sample_project["id"]

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, client: AsyncClient):
        """Test getting non-existent project returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"/api/projects/{fake_id}")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_project_name(self, client: AsyncClient, sample_project: dict):
        """Test updating project name."""
        new_name = f"Updated Name {uuid.uuid4()}"
        response = await client.patch(
            f"/api/projects/{sample_project['id']}",
            json={"name": new_name},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == new_name

    @pytest.mark.asyncio
    async def test_update_project_description(self, client: AsyncClient, sample_project: dict):
        """Test updating project description."""
        response = await client.patch(
            f"/api/projects/{sample_project['id']}",
            json={"description": "New description"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "New description"

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, client: AsyncClient):
        """Test updating non-existent project returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.patch(
            f"/api/projects/{fake_id}",
            json={"name": "New Name"},
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_success(self, client: AsyncClient, sample_project: dict):
        """Test deleting a project."""
        response = await client.delete(f"/api/projects/{sample_project['id']}")

        assert response.status_code == 200

        # Verify it's deleted
        get_response = await client.get(f"/api/projects/{sample_project['id']}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, client: AsyncClient):
        """Test deleting non-existent project returns 404."""
        fake_id = str(uuid.uuid4())
        response = await client.delete(f"/api/projects/{fake_id}")

        assert response.status_code == 404

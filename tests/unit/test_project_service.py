"""Tests for ProjectService."""
import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from services.project_service import ProjectService
from database.models import Project


class TestProjectServiceCreate:
    """Tests for ProjectService.create_project."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession) -> ProjectService:
        """Create ProjectService instance."""
        return ProjectService(db_session)

    @pytest.mark.asyncio
    async def test_create_project_success(self, service: ProjectService, db_session: AsyncSession):
        """Test creating a project successfully."""
        project = await service.create_project(
            name="My Test Project",
            description="Test description",
        )

        assert project.id is not None
        assert project.name == "My Test Project"
        assert project.description == "Test description"
        assert project.github_token is None
        assert project.github_repo is None

        # Verify it's in the database
        await db_session.refresh(project)
        assert project.id is not None

    @pytest.mark.asyncio
    async def test_create_project_without_description(self, service: ProjectService):
        """Test creating a project without description."""
        project = await service.create_project(name="No Description Project")

        assert project.name == "No Description Project"
        assert project.description is None


class TestProjectServiceGet:
    """Tests for ProjectService.get_project."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession) -> ProjectService:
        """Create ProjectService instance."""
        return ProjectService(db_session)

    @pytest.mark.asyncio
    async def test_get_project_success(
        self, service: ProjectService, sample_project: Project
    ):
        """Test getting an existing project."""
        project = await service.get_project(sample_project.id)

        assert project is not None
        assert project.id == sample_project.id
        assert project.name == sample_project.name

    @pytest.mark.asyncio
    async def test_get_project_not_found(self, service: ProjectService):
        """Test getting a non-existent project returns None."""
        project = await service.get_project(uuid.uuid4())

        assert project is None

    @pytest.mark.asyncio
    async def test_get_project_by_name_success(
        self, service: ProjectService, sample_project: Project
    ):
        """Test getting a project by name."""
        project = await service.get_project_by_name(sample_project.name)

        assert project is not None
        assert project.id == sample_project.id

    @pytest.mark.asyncio
    async def test_get_project_by_name_not_found(self, service: ProjectService):
        """Test getting a non-existent project by name returns None."""
        project = await service.get_project_by_name("NonExistent Project")

        assert project is None


class TestProjectServiceList:
    """Tests for ProjectService.list_projects."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession) -> ProjectService:
        """Create ProjectService instance."""
        return ProjectService(db_session)

    @pytest.mark.asyncio
    async def test_list_projects_empty(self, service: ProjectService):
        """Test listing projects when none exist."""
        projects = await service.list_projects()

        assert projects == []

    @pytest.mark.asyncio
    async def test_list_projects_multiple(
        self, service: ProjectService, db_session: AsyncSession
    ):
        """Test listing multiple projects."""
        # Create multiple projects
        await service.create_project(name="Project 1")
        await service.create_project(name="Project 2")
        await service.create_project(name="Project 3")

        projects = await service.list_projects()

        assert len(projects) == 3
        # Verify all projects are returned
        project_names = {p.name for p in projects}
        assert project_names == {"Project 1", "Project 2", "Project 3"}


class TestProjectServiceUpdate:
    """Tests for ProjectService.update_project."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession) -> ProjectService:
        """Create ProjectService instance."""
        return ProjectService(db_session)

    @pytest.mark.asyncio
    async def test_update_project_name(
        self, service: ProjectService, sample_project: Project
    ):
        """Test updating project name."""
        updated = await service.update_project(
            project_id=sample_project.id,
            name="Updated Name",
        )

        assert updated is not None
        assert updated.name == "Updated Name"
        assert updated.description == sample_project.description

    @pytest.mark.asyncio
    async def test_update_project_description(
        self, service: ProjectService, sample_project: Project
    ):
        """Test updating project description."""
        updated = await service.update_project(
            project_id=sample_project.id,
            description="New description",
        )

        assert updated is not None
        assert updated.name == sample_project.name
        assert updated.description == "New description"

    @pytest.mark.asyncio
    async def test_update_project_not_found(self, service: ProjectService):
        """Test updating non-existent project returns None."""
        updated = await service.update_project(
            project_id=uuid.uuid4(),
            name="New Name",
        )

        assert updated is None


class TestProjectServiceDelete:
    """Tests for ProjectService.delete_project."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession) -> ProjectService:
        """Create ProjectService instance."""
        return ProjectService(db_session)

    @pytest.mark.asyncio
    async def test_delete_project_success(
        self, service: ProjectService, sample_project: Project
    ):
        """Test deleting a project."""
        result = await service.delete_project(sample_project.id)

        assert result is True

        # Verify it's deleted
        project = await service.get_project(sample_project.id)
        assert project is None

    @pytest.mark.asyncio
    async def test_delete_project_not_found(self, service: ProjectService):
        """Test deleting non-existent project returns False."""
        result = await service.delete_project(uuid.uuid4())

        assert result is False

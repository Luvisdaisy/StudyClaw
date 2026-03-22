"""Tests for GitHubService."""
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from services.github_service import GitHubService, GitHubUser, GitHubRepo, GitHubFile, SyncResult
from database.models import Project, DocumentStatus


class TestGitHubServiceTokenValidation:
    """Tests for GitHub token validation."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession, sample_project: Project):
        """Create GitHubService instance."""
        return GitHubService(db_session, sample_project.id)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_validate_token_success(self, mock_client_class, service: GitHubService):
        """Test validating a valid token returns GitHubUser."""
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

        user = await service.validate_token("valid_token")

        assert isinstance(user, GitHubUser)
        assert user.login == "testuser"
        assert user.name == "Test User"
        assert user.avatar_url == "https://github.com/avatars/testuser.png"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_validate_token_invalid(self, mock_client_class, service: GitHubService):
        """Test validating invalid token raises ValueError."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.__aenter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(ValueError, match="Invalid GitHub token"):
            await service.validate_token("invalid_token")

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_validate_token_api_error(self, mock_client_class, service: GitHubService):
        """Test validating token with API error raises ValueError."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_client.__aenter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(ValueError, match="GitHub API error: 403"):
            await service.validate_token("valid_token")


class TestGitHubServiceListRepos:
    """Tests for listing repositories."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession, sample_project: Project):
        """Create GitHubService instance."""
        return GitHubService(db_session, sample_project.id)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_list_repos_success(self, mock_client_class, service: GitHubService):
        """Test listing repositories returns GitHubRepo list."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "full_name": "user/repo1",
                "name": "repo1",
                "description": "First repository",
                "default_branch": "main",
            },
            {
                "full_name": "user/repo2",
                "name": "repo2",
                "description": None,
                "default_branch": "develop",
            },
        ]
        mock_client.__aenter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        repos = await service.list_repos("valid_token")

        assert len(repos) == 2
        assert repos[0].full_name == "user/repo1"
        assert repos[0].name == "repo1"
        assert repos[1].default_branch == "develop"

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_list_repos_api_error(self, mock_client_class, service: GitHubService):
        """Test listing repos with API error raises ValueError."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_client.__aenter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        with pytest.raises(ValueError, match="GitHub API error: 401"):
            await service.list_repos("invalid_token")


class TestGitHubServiceFileTree:
    """Tests for getting file tree."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession, sample_project: Project):
        """Create GitHubService instance."""
        return GitHubService(db_session, sample_project.id)

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_file_tree_filters_supported_extensions(
        self, mock_client_class, service: GitHubService
    ):
        """Test file tree only includes supported file types."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"type": "file", "path": "readme.md", "size": 100, "sha": "abc123"},
            {"type": "file", "path": "script.js", "size": 200, "sha": "def456"},
            {"type": "file", "path": "docs.pdf", "size": 300, "sha": "ghi789"},
            {"type": "file", "path": "notes.txt", "size": 400, "sha": "jkl012"},
        ]
        mock_client.__aenter__.return_value.get.return_value = mock_response
        mock_client_class.return_value = mock_client

        files = await service.get_file_tree("token", "user/repo", "main")

        assert len(files) == 3
        paths = [f.path for f in files]
        assert "readme.md" in paths
        assert "docs.pdf" in paths
        assert "notes.txt" in paths
        assert "script.js" not in paths

    @pytest.mark.asyncio
    @patch("httpx.AsyncClient")
    async def test_get_file_tree_handles_directory(self, mock_client_class, service: GitHubService):
        """Test file tree recursively fetches subdirectories."""
        mock_client = AsyncMock()
        # First call returns root with directory
        # Second call returns subdirectory contents
        mock_response_1 = MagicMock(status_code=200)
        mock_response_1.json.return_value = [
            {"type": "dir", "path": "subdir"},
            {"type": "file", "path": "root.md", "size": 100, "sha": "abc123"},
        ]
        mock_response_2 = MagicMock(status_code=200)
        mock_response_2.json.return_value = [
            {"type": "file", "path": "subdir/nested.md", "size": 200, "sha": "def456"},
        ]
        mock_client.__aenter__.return_value.get.side_effect = [mock_response_1, mock_response_2]
        mock_client_class.return_value = mock_client

        files = await service.get_file_tree("token", "user/repo", "main")

        paths = [f.path for f in files]
        assert "root.md" in paths
        assert "subdir/nested.md" in paths


class TestGitHubServiceTokenStorage:
    """Tests for GitHub token storage."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession, sample_project: Project):
        """Create GitHubService instance."""
        return GitHubService(db_session, sample_project.id)

    @pytest.mark.asyncio
    async def test_save_and_get_token(self, service: GitHubService, db_session: AsyncSession):
        """Test saving and retrieving token."""
        await service.save_token("test_token_123")

        token = await service.get_token()
        assert token == "test_token_123"

    @pytest.mark.asyncio
    async def test_clear_token(self, service: GitHubService, db_session: AsyncSession):
        """Test clearing token."""
        await service.save_token("test_token_123")
        await service.clear_token()

        token = await service.get_token()
        assert token is None


class TestGitHubServiceRepoStorage:
    """Tests for repository storage."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession, sample_project: Project):
        """Create GitHubService instance."""
        return GitHubService(db_session, sample_project.id)

    @pytest.mark.asyncio
    async def test_save_and_get_repo_info(self, service: GitHubService, db_session: AsyncSession):
        """Test saving and retrieving repository info."""
        await service.save_repo("user/repo", "develop")

        repo_info = await service.get_repo_info()
        assert repo_info == ("user/repo", "develop")

    @pytest.mark.asyncio
    async def test_get_repo_info_when_none(self, service: GitHubService):
        """Test get_repo_info returns None when no repo set."""
        repo_info = await service.get_repo_info()
        assert repo_info is None

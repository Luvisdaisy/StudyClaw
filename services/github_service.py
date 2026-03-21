import logging
import uuid
import hashlib
import asyncio
from typing import Optional
from pathlib import Path
from dataclasses import dataclass
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader

from database.models import Document, DocumentStatus, Project
from utils.config_handler import chroma_cfg

logger = logging.getLogger(__name__)


@dataclass
class GitHubUser:
    login: str
    name: Optional[str]
    avatar_url: str


@dataclass
class GitHubRepo:
    full_name: str
    name: str
    description: Optional[str]
    default_branch: str


@dataclass
class GitHubFile:
    path: str
    size: int
    sha: str


@dataclass
class SyncResult:
    added: int
    skipped: int
    failed: int
    error: Optional[str] = None


class GitHubService:
    """Service for GitHub repository integration"""

    # File extensions to sync
    SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}

    def __init__(self, session: AsyncSession, project_id: uuid.UUID):
        self.session = session
        self.project_id = project_id
        self.data_dir = Path("data/projects") / str(project_id)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize text splitter (same as DocumentService)
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_cfg.get("chunk_size", 200),
            chunk_overlap=chroma_cfg.get("chunk_overlap", 20),
            separators=chroma_cfg.get("separators", ["\n\n", "\n", ".", "!", "?", "。", "！", "？", " ", ""]),
        )

    def _compute_file_hash(self, file_content: bytes) -> str:
        """Compute MD5 hash of file content"""
        return hashlib.md5(file_content).hexdigest()

    async def validate_token(self, token: str) -> GitHubUser:
        """Validate GitHub PAT and return user info"""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                timeout=10.0,
            )

            if response.status_code == 401:
                raise ValueError("Invalid GitHub token")
            if response.status_code != 200:
                raise ValueError(f"GitHub API error: {response.status_code}")

            data = response.json()
            return GitHubUser(
                login=data.get("login", ""),
                name=data.get("name"),
                avatar_url=data.get("avatar_url", ""),
            )

    async def list_repos(self, token: str) -> list[GitHubRepo]:
        """List all repositories for the authenticated user"""
        import httpx

        async with httpx.AsyncClient() as client:
            repos = []
            page = 1
            while True:
                response = await client.get(
                    "https://api.github.com/user/repos",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    params={"per_page": 100, "page": page, "sort": "updated"},
                    timeout=10.0,
                )

                if response.status_code != 200:
                    raise ValueError(f"GitHub API error: {response.status_code}")

                data = response.json()
                if not data:
                    break

                for repo in data:
                    repos.append(
                        GitHubRepo(
                            full_name=repo["full_name"],
                            name=repo["name"],
                            description=repo.get("description"),
                            default_branch=repo.get("default_branch", "main"),
                        )
                    )

                if len(data) < 100:
                    break
                page += 1

            return repos

    async def get_file_tree(
        self, token: str, repo_full_name: str, branch: str = "main"
    ) -> list[GitHubFile]:
        """Get file tree for a repository (only supported file types)"""
        import httpx

        owner, repo = repo_full_name.split("/", 1)

        async def fetch_tree(path: str = "") -> list[GitHubFile]:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github.v3+json",
                    },
                    params={"ref": branch},
                    timeout=30.0,
                )

                if response.status_code != 200:
                    return []

                items = response.json()
                if not isinstance(items, list):
                    return []

                files = []
                for item in items:
                    if item["type"] == "file":
                        ext = Path(item["path"]).suffix.lower()
                        if ext in self.SUPPORTED_EXTENSIONS:
                            files.append(
                                GitHubFile(
                                    path=item["path"],
                                    size=item.get("size", 0),
                                    sha=item.get("sha", ""),
                                )
                            )
                    elif item["type"] == "dir":
                        # Recursively fetch subdirectories
                        sub_files = await fetch_tree(item["path"])
                        files.extend(sub_files)

                return files

        return await fetch_tree()

    async def download_file(
        self, token: str, repo_full_name: str, path: str, branch: str = "main"
    ) -> bytes:
        """Download a single file from repository"""
        import httpx

        owner, repo = repo_full_name.split("/", 1)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.github.com/repos/{owner}/{repo}/contents/{path}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github.v3+json",
                },
                params={"ref": branch},
                timeout=30.0,
            )

            if response.status_code != 200:
                raise ValueError(f"Failed to download file: {response.status_code}")

            data = response.json()
            if data.get("encoding") == "base64":
                import base64

                return base64.b64decode(data["content"])
            else:
                raise ValueError("Unsupported encoding")

    def _sync_process_document(
        self, file_path: str, file_type: str, doc_id: str, project_id: str
    ) -> int:
        """Synchronous document processing for running in thread pool"""
        from rag.vector_store import VectorStoreService

        # Map file type to loader
        loaders = {
            "pdf": PyPDFLoader,
            "md": TextLoader,
            "txt": TextLoader,
        }

        loader_class = loaders.get(file_type)
        if not loader_class:
            raise ValueError(f"No loader for file type: {file_type}")

        loader = loader_class(file_path)
        documents = loader.load()

        if not documents:
            raise ValueError("No content loaded")

        # Split into chunks
        split_docs = self.splitter.split_documents(documents)
        if not split_docs:
            raise ValueError("Document splitting resulted in no chunks")

        # Add metadata
        for i, d in enumerate(split_docs):
            d.metadata["document_id"] = doc_id
            d.metadata["project_id"] = project_id
            d.metadata["chunk_index"] = i

        # Add to vector store
        vector_store = VectorStoreService(project_id=uuid.UUID(project_id))
        vector_store.add_documents(split_docs)

        return len(split_docs)

    async def _check_hash_exists(self, file_hash: str) -> bool:
        """Check if a document with this hash already exists in the project"""
        result = await self.session.execute(
            select(Document).where(
                Document.project_id == self.project_id,
                Document.file_hash == file_hash,
            )
        )
        return result.scalar_one_or_none() is not None

    async def _save_document(
        self, filename: str, file_content: bytes, file_type: str, file_hash: str
    ) -> Document:
        """Save a document to disk and database"""
        # Generate safe filename
        safe_filename = f"{uuid.uuid4()}.{file_type}"
        file_path = self.data_dir / safe_filename

        with open(file_path, "wb") as f:
            f.write(file_content)

        doc = Document(
            id=uuid.uuid4(),
            project_id=self.project_id,
            filename=filename,
            file_path=str(file_path),
            file_type=file_type,
            file_hash=file_hash,
            status=DocumentStatus.PENDING,
        )
        self.session.add(doc)
        await self.session.commit()

        return doc

    async def sync_repo(
        self, token: str, repo_full_name: str, branch: str = "main"
    ) -> SyncResult:
        """Sync repository files to project knowledge base"""
        result = SyncResult(added=0, skipped=0, failed=0)

        try:
            # Get file tree
            files = await self.get_file_tree(token, repo_full_name, branch)

            for file_info in files:
                try:
                    # Download file
                    content = await self.download_file(
                        token, repo_full_name, file_info.path, branch
                    )

                    # Compute hash
                    file_hash = self._compute_file_hash(content)

                    # Check if already exists
                    if await self._check_hash_exists(file_hash):
                        result.skipped += 1
                        continue

                    # Get file type
                    ext = Path(file_info.path).suffix.lower()[1:]  # Remove the dot

                    # Save document
                    doc = await self._save_document(
                        filename=file_info.path.split("/")[-1],
                        file_content=content,
                        file_type=ext,
                        file_hash=file_hash,
                    )

                    # Process document (add to vector store)
                    await asyncio.to_thread(
                        self._sync_process_document,
                        str(doc.file_path),
                        ext,
                        str(doc.id),
                        str(self.project_id),
                    )

                    # Update document status
                    doc.status = DocumentStatus.COMPLETED
                    doc.chunk_count = await self._get_chunk_count(doc.id)
                    await self.session.commit()

                    result.added += 1

                except Exception as e:
                    logger.error(f"Failed to sync file {file_info.path}: {e}")
                    result.failed += 1
                    continue

        except Exception as e:
            logger.error(f"Sync failed: {e}")
            result.error = str(e)

        return result

    async def _get_chunk_count(self, doc_id: uuid.UUID) -> int:
        """Get chunk count for a document from vector store"""
        # This is a simplified approach - in production you might track this differently
        from rag.vector_store import VectorStoreService

        try:
            vector_store = VectorStoreService(project_id=self.project_id)
            # Count documents with this document_id in metadata
            return len(vector_store.get_by_document_id(str(doc_id)))
        except Exception:
            return 0

    async def save_token(self, token: str) -> None:
        """Save GitHub token to project"""
        project = await self.session.get(Project, self.project_id)
        if project:
            project.github_token = token
            await self.session.commit()

    async def clear_token(self) -> None:
        """Clear GitHub token from project"""
        project = await self.session.get(Project, self.project_id)
        if project:
            project.github_token = None
            project.github_repo = None
            await self.session.commit()

    async def get_token(self) -> Optional[str]:
        """Get stored GitHub token"""
        project = await self.session.get(Project, self.project_id)
        return project.github_token if project else None

    async def save_repo(self, repo_full_name: str, default_branch: str) -> None:
        """Save selected repository to project"""
        project = await self.session.get(Project, self.project_id)
        if project:
            project.github_repo = f"{repo_full_name}:{default_branch}"
            await self.session.commit()

    async def get_repo_info(self) -> Optional[tuple[str, str]]:
        """Get stored repository info (full_name, branch)"""
        project = await self.session.get(Project, self.project_id)
        if project and project.github_repo:
            parts = project.github_repo.split(":", 1)
            if len(parts) == 2:
                return (parts[0], parts[1])
        return None

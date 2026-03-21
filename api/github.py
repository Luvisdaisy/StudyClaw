import uuid
from typing import Optional
from enum import Enum
from dataclasses import dataclass, field
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database.session import get_db
from services.github_service import GitHubService, SyncResult

router = APIRouter(prefix="/api/projects", tags=["github"])


# In-memory sync status storage (per project)
# In production, this would be Redis or database-backed
class SyncStatus(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SyncState:
    status: SyncStatus = SyncStatus.IDLE
    result: Optional[SyncResult] = None


_sync_states: dict[str, SyncState] = {}


def get_sync_state(project_id: str) -> SyncState:
    if project_id not in _sync_states:
        _sync_states[project_id] = SyncState()
    return _sync_states[project_id]


# Request/Response models
class GitHubConnectRequest(BaseModel):
    token: str


class GitHubUserResponse(BaseModel):
    login: str
    name: Optional[str]
    avatar_url: str


class GitHubRepoResponse(BaseModel):
    full_name: str
    name: str
    description: Optional[str]
    default_branch: str


class GitHubRepoSelectRequest(BaseModel):
    repo_full_name: str
    default_branch: str = "main"


class GitHubSyncStatusResponse(BaseModel):
    status: str
    added: Optional[int] = None
    skipped: Optional[int] = None
    failed: Optional[int] = None
    error: Optional[str] = None


async def run_sync(project_id: str, token: str, repo_full_name: str, branch: str):
    """Background task to run repository sync"""
    from database.session import get_db_context

    state = get_sync_state(project_id)
    state.status = SyncStatus.RUNNING
    state.result = None

    try:
        async with get_db_context() as session:
            service = GitHubService(session, uuid.UUID(project_id))
            result = await service.sync_repo(token, repo_full_name, branch)
            state.result = result
            state.status = SyncStatus.COMPLETED if result.error is None else SyncStatus.FAILED
    except Exception as e:
        state.status = SyncStatus.FAILED
        state.result = SyncResult(added=0, skipped=0, failed=0, error=str(e))


@router.post("/{project_id}/github/connect", response_model=GitHubUserResponse)
async def connect_github(
    project_id: uuid.UUID,
    request: GitHubConnectRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate GitHub PAT and save to project"""
    service = GitHubService(db, project_id)

    try:
        user = await service.validate_token(request.token)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save token
    await service.save_token(request.token)

    return GitHubUserResponse(
        login=user.login,
        name=user.name,
        avatar_url=user.avatar_url,
    )


@router.post("/{project_id}/github/disconnect")
async def disconnect_github(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Remove GitHub token and repo from project"""
    service = GitHubService(db, project_id)
    await service.clear_token()

    # Clear sync state
    if str(project_id) in _sync_states:
        del _sync_states[str(project_id)]

    return {"message": "GitHub disconnected successfully"}


@router.get("/{project_id}/github/repos", response_model=list[GitHubRepoResponse])
async def list_github_repos(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all repositories for connected GitHub account"""
    service = GitHubService(db, project_id)

    token = await service.get_token()
    if not token:
        raise HTTPException(status_code=400, detail="GitHub not connected")

    try:
        repos = await service.list_repos(token)
        return [
            GitHubRepoResponse(
                full_name=repo.full_name,
                name=repo.name,
                description=repo.description,
                default_branch=repo.default_branch,
            )
            for repo in repos
        ]
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{project_id}/github/repo")
async def select_github_repo(
    project_id: uuid.UUID,
    request: GitHubRepoSelectRequest,
    db: AsyncSession = Depends(get_db),
):
    """Select repository for sync"""
    service = GitHubService(db, project_id)

    token = await service.get_token()
    if not token:
        raise HTTPException(status_code=400, detail="GitHub not connected")

    await service.save_repo(request.repo_full_name, request.default_branch)

    return {"message": "Repository selected", "repo": request.repo_full_name}


@router.post("/{project_id}/github/sync")
async def trigger_github_sync(
    project_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """Trigger repository sync (runs in background)"""
    service = GitHubService(db, project_id)

    token = await service.get_token()
    if not token:
        raise HTTPException(status_code=400, detail="GitHub not connected")

    repo_info = await service.get_repo_info()
    if not repo_info:
        raise HTTPException(status_code=400, detail="No repository selected")

    repo_full_name, branch = repo_info

    # Check if already running
    state = get_sync_state(str(project_id))
    if state.status == SyncStatus.RUNNING:
        raise HTTPException(status_code=409, detail="Sync already in progress")

    # Reset state
    state.status = SyncStatus.IDLE
    state.result = None

    # Run in background
    background_tasks.add_task(run_sync, str(project_id), token, repo_full_name, branch)

    return {"message": "Sync started"}


@router.get("/{project_id}/github/sync/status", response_model=GitHubSyncStatusResponse)
async def get_sync_status(
    project_id: uuid.UUID,
):
    """Get current sync status"""
    state = get_sync_state(str(project_id))

    return GitHubSyncStatusResponse(
        status=state.status.value,
        added=state.result.added if state.result else None,
        skipped=state.result.skipped if state.result else None,
        failed=state.result.failed if state.result else None,
        error=state.result.error if state.result else None,
    )


@router.get("/{project_id}/github/user", response_model=Optional[GitHubUserResponse])
async def get_github_user(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get connected GitHub user info (if connected)"""
    service = GitHubService(db, project_id)

    token = await service.get_token()
    if not token:
        return None

    try:
        user = await service.validate_token(token)
        return GitHubUserResponse(
            login=user.login,
            name=user.name,
            avatar_url=user.avatar_url,
        )
    except ValueError:
        return None

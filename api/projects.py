import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from database.session import get_db
from services.project_service import ProjectService

router = APIRouter(prefix="/api/projects", tags=["projects"])


# Request/Response models
class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    github_token: Optional[str] = None
    github_repo: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    github_repo: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]


@router.post("", response_model=ProjectResponse)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new project"""
    service = ProjectService(db)

    # Check if project with same name exists
    existing = await service.get_project_by_name(project_data.name)
    if existing:
        raise HTTPException(status_code=400, detail="Project with this name already exists")

    project = await service.create_project(
        name=project_data.name,
        description=project_data.description,
    )
    return ProjectResponse(**project.to_dict())


@router.get("", response_model=ProjectListResponse)
async def list_projects(db: AsyncSession = Depends(get_db)):
    """List all projects"""
    service = ProjectService(db)
    projects = await service.list_projects()
    return ProjectListResponse(
        projects=[ProjectResponse(**p.to_dict()) for p in projects]
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Get project by ID"""
    service = ProjectService(db)
    project = await service.get_project(project_id)

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(**project.to_dict())


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: uuid.UUID,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update project"""
    service = ProjectService(db)

    # Check if name already taken by another project
    if project_data.name:
        existing = await service.get_project_by_name(project_data.name)
        if existing and existing.id != project_id:
            raise HTTPException(status_code=400, detail="Project name already exists")

    project = await service.update_project(
        project_id=project_id,
        name=project_data.name,
        description=project_data.description,
        github_token=project_data.github_token,
        github_repo=project_data.github_repo,
    )

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse(**project.to_dict())


@router.delete("/{project_id}")
async def delete_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Delete project and all associated documents"""
    service = ProjectService(db)

    # Clean up vector store
    try:
        from agent.tools.rag_tool import clear_rag_service
        clear_rag_service(project_id)

        from rag.vector_store import VectorStoreService
        vs = VectorStoreService(project_id=project_id)
        vs.delete_all()
    except Exception:
        pass  # Continue even if cleanup fails

    success = await service.delete_project(project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")

    return {"message": "Project deleted successfully"}

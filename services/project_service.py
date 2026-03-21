import uuid
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import Project


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_project(self, name: str, description: Optional[str] = None) -> Project:
        """Create a new project"""
        project = Project(
            id=uuid.uuid4(),
            name=name,
            description=description,
        )
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def get_project(self, project_id: uuid.UUID) -> Optional[Project]:
        """Get project by ID"""
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_project_by_name(self, name: str) -> Optional[Project]:
        """Get project by name"""
        result = await self.session.execute(
            select(Project).where(Project.name == name)
        )
        return result.scalar_one_or_none()

    async def list_projects(self) -> list[Project]:
        """List all projects"""
        result = await self.session.execute(
            select(Project).order_by(Project.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_project(
        self,
        project_id: uuid.UUID,
        name: Optional[str] = None,
        description: Optional[str] = None,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None,
    ) -> Optional[Project]:
        """Update project"""
        project = await self.get_project(project_id)
        if not project:
            return None

        if name is not None:
            project.name = name
        if description is not None:
            project.description = description
        if github_token is not None:
            project.github_token = github_token
        if github_repo is not None:
            project.github_repo = github_repo

        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def delete_project(self, project_id: uuid.UUID) -> bool:
        """Delete project and all associated documents"""
        result = await self.session.execute(
            delete(Project).where(Project.id == project_id)
        )
        await self.session.commit()
        return result.rowcount > 0

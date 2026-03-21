"""Shared dependencies for API routes."""
import uuid
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database.session import get_db
from services.project_service import ProjectService
from database.models import Project, Document


async def get_project_service(db: AsyncSession) -> ProjectService:
    """Get ProjectService instance."""
    return ProjectService(db)


async def get_project(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Project:
    """
    Validate project exists and return it.

    Use this dependency when you need to ensure a project exists
    before performing operations on it.
    """
    service = ProjectService(db)
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def get_document_by_id(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Document:
    """
    Fetch a document by ID.

    Raises 404 if document doesn't exist.
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

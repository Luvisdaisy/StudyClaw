import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from database.session import get_db
from services.document_service import DocumentService
from services.project_service import ProjectService
from database.models import Document

router = APIRouter(prefix="/api", tags=["documents"])


# Response models
class DocumentResponse(BaseModel):
    id: str
    project_id: str
    filename: str
    file_type: str
    status: str
    chunk_count: int
    created_at: Optional[str]
    updated_at: Optional[str]


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]


class MessageResponse(BaseModel):
    message: str


@router.post("/projects/{project_id}/documents", response_model=DocumentResponse)
async def upload_document(
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """Upload a document to a project"""
    # Check project exists
    project_service = ProjectService(db)
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Validate file type
    allowed_types = {"pdf", "md", "txt"}
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Supported: {', '.join(allowed_types)}"
        )

    # Read file content
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    # Upload and process
    doc_service = DocumentService(db, project_id)
    try:
        doc = await doc_service.upload_document(content, file.filename)
        return DocumentResponse(**doc.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process document: {str(e)}\n{traceback.format_exc()}")


@router.get("/projects/{project_id}/documents", response_model=DocumentListResponse)
async def list_documents(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all documents in a project"""
    # Check project exists
    project_service = ProjectService(db)
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    doc_service = DocumentService(db, project_id)
    documents = await doc_service.list_documents()

    return DocumentListResponse(
        documents=[DocumentResponse(**d.to_dict()) for d in documents]
    )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get document by ID"""
    from sqlalchemy import select

    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentResponse(**doc.to_dict())


@router.delete("/documents/{document_id}", response_model=MessageResponse)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a document"""
    # Get document to find project_id
    from sqlalchemy import select

    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    doc = result.scalar_one_or_none()

    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    doc_service = DocumentService(db, doc.project_id)
    success = await doc_service.delete_document(document_id)

    if not success:
        raise HTTPException(status_code=404, detail="Document not found")

    return MessageResponse(message="Document deleted successfully")

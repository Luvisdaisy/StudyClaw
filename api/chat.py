import uuid
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional

from database.session import get_db
from services.project_service import ProjectService
from agent.react_agent import ProjectAgentFactory
from session_store.manager import get_session_manager

router = APIRouter(prefix="/api/projects", tags=["chat"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    enable_web_search: bool = False


class ChatResponse(BaseModel):
    response: str


class SessionSummary(BaseModel):
    session_id: str
    title: str
    updated_at: Optional[str] = None


class SessionDetail(BaseModel):
    session_id: str
    title: str
    messages: list[dict]
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SessionListResponse(BaseModel):
    sessions: list[SessionSummary]
    total: int


@router.post("/{project_id}/chat")
async def chat(
    project_id: uuid.UUID,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Chat with RAG assistant for a project.
    Returns streaming response.
    """
    # Check project exists
    project_service = ProjectService(db)
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get or create agent for this project
    agent = ProjectAgentFactory.get_agent(str(project_id), request.enable_web_search)

    # Use session_id or generate one
    session_id = request.session_id or str(uuid.uuid4())

    async def generate():
        try:
            async for chunk in agent.async_execute_stream(request.message, session_id):
                if chunk:
                    # Send as SSE format
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
            # Send completion signal
            yield f"data: {json.dumps({'content': '', 'done': True})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/{project_id}/chat/sessions")
async def list_chat_sessions(
    project_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions for a project"""
    project_service = ProjectService(db)
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    manager = get_session_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Session manager not initialized")

    sessions = await manager.pg.load_by_project(str(project_id))
    return SessionListResponse(
        sessions=[
            SessionSummary(
                session_id=s["session_id"],
                title=s.get("title", ""),
                updated_at=s.get("updated_at"),
            )
            for s in sessions
        ],
        total=len(sessions),
    )


@router.get("/{project_id}/chat/sessions/{session_id}")
async def get_chat_session(
    project_id: uuid.UUID,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific chat session with messages"""
    project_service = ProjectService(db)
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    manager = get_session_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Session manager not initialized")

    messages = await manager.load(session_id)
    if messages is None:
        raise HTTPException(status_code=404, detail="Session not found")

    session_data = await manager.pg.get_session(session_id)
    title = session_data.get("title", "") if session_data else ""
    created_at = session_data.get("created_at") if session_data else None
    updated_at = session_data.get("updated_at") if session_data else None

    return SessionDetail(
        session_id=session_id,
        title=title,
        messages=messages,
        created_at=created_at,
        updated_at=updated_at,
    )


@router.delete("/{project_id}/chat/sessions/{session_id}")
async def delete_chat_session(
    project_id: uuid.UUID,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Delete a chat session"""
    project_service = ProjectService(db)
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    manager = get_session_manager()
    if not manager:
        raise HTTPException(status_code=503, detail="Session manager not initialized")

    await manager.delete(session_id)
    return {"message": "Session deleted"}

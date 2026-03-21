import uuid
import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional

from database.session import get_db
from services.project_service import ProjectService
from agent.react_agent import ProjectAgentFactory

router = APIRouter(prefix="/api/projects", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str


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
    agent = ProjectAgentFactory.get_agent(str(project_id))

    # Use session_id or generate one
    session_id = request.session_id or str(uuid.uuid4())

    async def generate():
        try:
            for chunk in agent.execute_stream(request.message, session_id=session_id):
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


@router.get("/{project_id}/chat/history")
async def get_chat_history(
    project_id: uuid.UUID,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get chat history for a session (placeholder for future implementation)"""
    # Check project exists
    project_service = ProjectService(db)
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # TODO: Implement session history storage
    return {"session_id": session_id, "messages": []}


@router.delete("/{project_id}/chat/history")
async def clear_chat_history(
    project_id: uuid.UUID,
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Clear chat history for a session"""
    # Check project exists
    project_service = ProjectService(db)
    project = await project_service.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Clear agent session
    ProjectAgentFactory.clear_agent(str(project_id))

    return {"message": "Chat history cleared"}

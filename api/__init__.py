from .projects import router as projects_router
from .documents import router as documents_router
from .chat import router as chat_router
from .github import router as github_router

__all__ = ["projects_router", "documents_router", "chat_router", "github_router"]

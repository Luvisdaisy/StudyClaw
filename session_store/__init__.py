"""Session persistence module for StudyClaw

Provides Redis (primary, TTL=7d) + PostgreSQL (backup) session storage.
"""

from .manager import SessionManager, get_session_manager, init_session_manager, shutdown_session_manager
from .checkpoint import SessionCheckpointSaver, get_session_checkpoint_saver

__all__ = [
    "SessionManager",
    "get_session_manager",
    "init_session_manager",
    "shutdown_session_manager",
    "SessionCheckpointSaver",
    "get_session_checkpoint_saver",
]

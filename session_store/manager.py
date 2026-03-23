"""Session Manager - unified interface with async PostgreSQL sync"""

import asyncio
import json
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from .redis_store import RedisStore
from .postgres_store import PostgresStore

logger = logging.getLogger(__name__)


@dataclass
class PendingSession:
    """Session pending PostgreSQL sync"""
    session_id: str
    project_id: str
    messages: list[dict]
    title: str = ""
    updated_at: datetime = field(default_factory=datetime.now)


class SessionManager:
    """
    Unified session manager with Redis (primary) + PostgreSQL (backup).

    Write flow: Agent -> SessionManager.save() -> Redis (sync, TTL=7d)
                                                    -> PostgreSQL (async batch)

    Read flow: Agent -> SessionManager.load() -> Redis (priority)
                                                -> PostgreSQL (fallback, repopulate Redis)
    """

    def __init__(
        self,
        redis_store: RedisStore,
        postgres_store: PostgresStore,
        batch_interval: int = 60,
        batch_size: int = 100,
    ):
        self.redis = redis_store
        self.pg = postgres_store
        self.batch_interval = batch_interval
        self.batch_size = batch_size

        # Pending sessions for async PostgreSQL sync
        self._pending: dict[str, PendingSession] = {}
        self._pending_lock = asyncio.Lock()
        self._sync_task: Optional[asyncio.Task] = None
        self._running = False

    async def start(self):
        """Start background sync task"""
        if self._running:
            return
        self._running = True
        # Initialize PostgreSQL schema
        await self.pg.init_schema()
        # Start background sync task
        self._sync_task = asyncio.create_task(self._sync_loop())
        logger.info("SessionManager started")

    async def stop(self):
        """Stop background sync and flush pending sessions"""
        self._running = False
        if self._sync_task:
            self._sync_task.cancel()
            try:
                await self._sync_task
            except asyncio.CancelledError:
                pass
        # Flush remaining pending sessions
        await self._flush_pending()
        logger.info("SessionManager stopped")

    async def save(self, session_id: str, project_id: str, messages: list[dict]) -> bool:
        """
        Save session to Redis (sync) and queue for PostgreSQL (async).
        Derives title from first user message if session is new (messages was empty).
        """
        # Derive title from first user message
        title = self._derive_title(messages)

        # Save to Redis (primary storage)
        redis_ok = await self.redis.save(session_id, messages, title)

        # Queue for PostgreSQL sync
        async with self._pending_lock:
            self._pending[session_id] = PendingSession(
                session_id=session_id,
                project_id=project_id,
                messages=messages,
                title=title,
            )

        # Trigger sync if batch size reached
        async with self._pending_lock:
            if len(self._pending) >= self.batch_size:
                asyncio.create_task(self._flush_pending())

        return redis_ok

    def _derive_title(self, messages: list[dict]) -> str:
        """Derive session title from first user message."""
        for msg in messages:
            # Handle both flat and nested message formats from LangChain
            # Flat format: {"type": "human", "content": "..."}
            # Nested format: {"type": "human", "data": {"content": "..."}}
            msg_type = msg.get("role") or msg.get("type")
            if msg_type == "human":
                content = msg.get("content") or msg.get("data", {}).get("content")
                if content:
                    return content[:100] if len(content) > 100 else content
        return ""

    async def load(self, session_id: str) -> Optional[list[dict]]:
        """
        Load session from Redis (priority), fallback to PostgreSQL.
        If found in PostgreSQL but not Redis, repopulate Redis.
        """
        # Try Redis first
        messages = await self.redis.load(session_id)
        if messages is not None:
            return messages

        # Fallback to PostgreSQL
        messages = await self.pg.load(session_id)
        if messages is not None:
            # Repopulate Redis for future reads
            asyncio.create_task(self.redis.save(session_id, messages))
            logger.info(f"Repopulated Redis with session {session_id} from PostgreSQL")
            return messages

        return None

    async def delete(self, session_id: str) -> bool:
        """Delete session from both Redis and PostgreSQL"""
        redis_ok = await self.redis.delete(session_id)

        # Remove from pending if queued
        async with self._pending_lock:
            self._pending.pop(session_id, None)

        # Delete from PostgreSQL
        await self.pg.delete(session_id)

        return redis_ok

    async def _sync_loop(self):
        """Background loop: periodic flush to PostgreSQL"""
        while self._running:
            try:
                await asyncio.sleep(self.batch_interval)
                if self._running:
                    await self._flush_pending()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in sync loop: {e}")

    async def _flush_pending(self):
        """Flush all pending sessions to PostgreSQL"""
        async with self._pending_lock:
            if not self._pending:
                return
            sessions = [
                {
                    "session_id": s.session_id,
                    "project_id": s.project_id,
                    "messages": s.messages,
                    "title": s.title,
                }
                for s in self._pending.values()
            ]
            self._pending.clear()

        if sessions:
            await self.pg.batch_save(sessions)
            logger.debug(f"Flushed {len(sessions)} sessions to PostgreSQL")

    # ----- LangGraph Checkpoint Compatibility -----

    async def get(self, session_id: str) -> Optional[dict]:
        """
        Get checkpoint data for LangGraph (mimics MemorySaver.get).
        Returns dict with 'v': 1, 'id': session_id, 'bianry_data': serialized messages.
        """
        messages = await self.load(session_id)
        if messages is None:
            return None
        # Serialize for LangGraph checkpoint format
        serialized = json.dumps(messages, ensure_ascii=False)
        return {
            "v": 1,
            "id": session_id,
            "binary_data": serialized.encode("utf-8"),
        }

    async def put(self, session_id: str, project_id: str, messages: list[dict]) -> dict:
        """
        Put checkpoint data for LangGraph (mimics MemorySaver.put).
        Returns config dict with checkpoint_id.
        """
        await self.save(session_id, project_id, messages)
        return {
            "configurable": {
                "thread_id": session_id,
                "project_id": project_id,
                "checkpoint_id": session_id,
            }
        }

    async def append_writes(self, session_id: str, project_id: str, writes: list) -> bool:
        """Store intermediate writes to Redis"""
        return await self.redis.append_writes(session_id, project_id, writes)


# Global instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> Optional[SessionManager]:
    """Get global SessionManager instance"""
    return _session_manager


async def init_session_manager(
    redis_host: str = "localhost",
    redis_port: int = 6379,
    redis_db: int = 0,
    redis_password: Optional[str] = None,
    async_session_factory=None,
    batch_interval: int = 60,
    batch_size: int = 100,
) -> SessionManager:
    """
    Initialize global SessionManager.

    Args:
        redis_host: Redis host
        redis_port: Redis port
        redis_db: Redis database number
        redis_password: Redis password (optional)
        async_session_factory: SQLAlchemy async session factory
        batch_interval: Seconds between PostgreSQL sync (default 60)
        batch_size: Number of sessions to trigger immediate sync (default 100)

    Returns:
        Initialized SessionManager
    """
    global _session_manager

    redis_store = RedisStore(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        password=redis_password,
    )
    postgres_store = PostgresStore(async_session_factory)

    _session_manager = SessionManager(
        redis_store=redis_store,
        postgres_store=postgres_store,
        batch_interval=batch_interval,
        batch_size=batch_size,
    )

    await _session_manager.start()
    return _session_manager


async def shutdown_session_manager():
    """Shutdown global SessionManager"""
    global _session_manager
    if _session_manager:
        await _session_manager.stop()
        _session_manager = None

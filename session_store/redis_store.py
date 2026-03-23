"""Redis session store - primary storage with TTL=7 days"""

import json
import logging
from collections import deque
from typing import Optional

import redis.asyncio as redis
from langchain_core.messages import BaseMessage

logger = logging.getLogger(__name__)

SESSION_TTL = 7 * 24 * 60 * 60  # 7 days in seconds


def _normalize_deques(obj):
    """Recursively convert deque and LangChain messages to JSON-serializable format."""
    # Handle LangChain message types
    if isinstance(obj, BaseMessage):
        return {
            "type": obj.type,
            "content": obj.content,
            "name": getattr(obj, "name", None),
            "id": getattr(obj, "id", None),
            "additional_kwargs": obj.additional_kwargs,
        }
    if isinstance(obj, deque):
        return [_normalize_deques(item) for item in obj]
    elif isinstance(obj, tuple):
        return [_normalize_deques(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: _normalize_deques(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_normalize_deques(item) for item in obj]
    return obj


class RedisStore:
    """Redis-based session storage"""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        prefix: str = "session:",
    ):
        self.prefix = prefix
        self._client: Optional[redis.Redis] = None
        self._config = {
            "host": host,
            "port": port,
            "db": db,
            "password": password,
            "decode_responses": True,
        }

    async def _get_client(self) -> redis.Redis:
        """Get or create Redis client"""
        if self._client is None:
            self._client = redis.Redis(**self._config)
        return self._client

    def _make_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"{self.prefix}{session_id}"

    async def save(self, session_id: str, messages: list[dict]) -> bool:
        """Save session messages to Redis"""
        try:
            client = await self._get_client()
            key = self._make_key(session_id)
            data = json.dumps(messages, ensure_ascii=False)
            await client.setex(key, SESSION_TTL, data)
            logger.debug(f"Saved session {session_id} to Redis (TTL={SESSION_TTL}s)")
            return True
        except Exception as e:
            logger.error(f"Failed to save session {session_id} to Redis: {e}")
            return False

    async def load(self, session_id: str) -> Optional[list[dict]]:
        """Load session messages from Redis"""
        try:
            client = await self._get_client()
            key = self._make_key(session_id)
            data = await client.get(key)
            if data:
                logger.debug(f"Loaded session {session_id} from Redis")
                return json.loads(data)
            logger.debug(f"Session {session_id} not found in Redis")
            return None
        except Exception as e:
            logger.error(f"Failed to load session {session_id} from Redis: {e}")
            return None

    async def delete(self, session_id: str) -> bool:
        """Delete session from Redis"""
        try:
            client = await self._get_client()
            key = self._make_key(session_id)
            await client.delete(key)
            logger.debug(f"Deleted session {session_id} from Redis")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id} from Redis: {e}")
            return False

    async def exists(self, session_id: str) -> bool:
        """Check if session exists in Redis"""
        try:
            client = await self._get_client()
            key = self._make_key(session_id)
            return await client.exists(key) > 0
        except Exception as e:
            logger.error(f"Failed to check session {session_id} in Redis: {e}")
            return False

    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.close()
            self._client = None

    async def append_writes(self, session_id: str, task_id: str, writes: list) -> bool:
        """Append intermediate writes to Redis with separate key pattern"""
        try:
            client = await self._get_client()
            key = f"writes:{self.prefix}{session_id}:{task_id}"
            normalized = _normalize_deques(writes)
            data = json.dumps(normalized, ensure_ascii=False)
            await client.setex(key, SESSION_TTL, data)
            logger.debug(f"Saved writes for session {session_id}, task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save writes for {session_id}:{task_id}: {e}")
            return False

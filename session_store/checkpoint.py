"""LangGraph Checkpoint adapter for SessionManager

Provides LangGraph-compatible checkpoint interface using SessionManager backend.
"""

import asyncio
import json
import logging
import threading
import time
from typing import Optional, Any

from langgraph.checkpoint.base import BaseCheckpointSaver, CheckpointTuple
from langgraph.types import CheckpointMetadata

from .manager import get_session_manager

logger = logging.getLogger(__name__)


class _AsyncRunner:
    """Dedicated thread with persistent event loop for sync-to-async bridging."""

    def __init__(self):
        self._thread = None
        self._loop = None
        self._started = False
        self._lock = threading.Lock()

    def _run_loop(self):
        """Thread target - runs forever event loop."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    def start(self):
        with self._lock:
            if not self._started:
                self._thread = threading.Thread(target=self._run_loop, daemon=True)
                self._thread.start()
                self._started = True

    def run_async(self, coro):
        """Run async coroutine in the dedicated thread's event loop."""
        if not self._loop:
            raise RuntimeError("AsyncRunner not started")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=30)


# Global async runner for sync-to-async bridging
_async_runner = _AsyncRunner()


class SessionCheckpointSaver(BaseCheckpointSaver):
    """
    LangGraph CheckpointSaver backed by SessionManager (Redis + PostgreSQL).

    This adapter provides the standard LangGraph checkpoint interface while
    using SessionManager for actual storage.
    """

    def __init__(self):
        super().__init__()
        # LangGraph expects these attributes:
        self.readonly = False

    @property
    def manager(self):
        """Get SessionManager instance"""
        return get_session_manager()

    async def aget_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """
        Async get checkpoint tuple - called by LangGraph's AsyncPregelLoop.
        """
        thread_id = config.get("configurable", {}).get("thread_id")

        if not self.manager:
            return None

        if not thread_id:
            return None

        checkpoint_data = await self.manager.get(thread_id)
        if checkpoint_data:
            checkpoint = json.loads(checkpoint_data["binary_data"].decode("utf-8"))
            return CheckpointTuple(
                config=config,
                checkpoint=checkpoint,
                metadata={},
                parent_config=None,
                pending_writes=None,
            )
        return None

    async def aput(
        self,
        config: dict,
        checkpoint: Any,
        metadata: CheckpointMetadata,
        new_versions: dict = None,
    ) -> dict:
        """
        Async put checkpoint - called by LangGraph's AsyncPregelLoop.
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        project_id = config.get("configurable", {}).get("project_id", "default")

        if not self.manager:
            return config

        if thread_id:
            # checkpoint is the serialized state (messages list)
            messages = checkpoint.get("messages", checkpoint) if hasattr(checkpoint, "get") else checkpoint.get("messages", [])
            if isinstance(messages, list):
                await self.manager.put(thread_id, project_id, messages)

        return {
            "configurable": {
                **config.get("configurable", {}),
                "checkpoint_id": thread_id,
            }
        }

    def get_tuple(self, config: dict) -> Optional[CheckpointTuple]:
        """
        Sync version - runs async aget_tuple via dedicated event loop runner.
        Called by LangGraph's SyncPregelLoop.
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        logger.info(f"[CHECKPOINT get_tuple SYNC] Called for thread_id={thread_id}")

        if not thread_id or not self.manager:
            return None

        checkpoint_data = _async_runner.run_async(self.manager.get(thread_id))
        if checkpoint_data:
            checkpoint = json.loads(checkpoint_data["binary_data"].decode("utf-8"))
            return CheckpointTuple(
                config=config,
                checkpoint=checkpoint,
                metadata={},
                parent_config=None,
                pending_writes=None,
            )
        return None

    def put(
        self,
        config: dict,
        checkpoint: Any,
        metadata: CheckpointMetadata = None,
        new_versions: dict = None,
    ) -> dict:
        """
        Sync version - runs async aput via dedicated event loop runner.
        Called by LangGraph's SyncPregelLoop.
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        project_id = config.get("configurable", {}).get("project_id", "default")
        logger.info(f"[CHECKPOINT put SYNC] thread_id={thread_id}, project_id={project_id}")

        if thread_id and self.manager:
            messages = checkpoint.get("messages", checkpoint) if hasattr(checkpoint, "get") else checkpoint.get("messages", [])
            if isinstance(messages, list):
                logger.info(f"[CHECKPOINT put SYNC] Saving {len(messages)} messages")
                _async_runner.run_async(
                    self.manager.put(thread_id, project_id, messages)
                )

        return {
            "configurable": {
                **config.get("configurable", {}),
                "checkpoint_id": thread_id,
            }
        }

    def put_writes(self, config: dict, writes: list, task_id: str, task_path: str = "") -> None:
        """
        Store intermediate writes linked to a checkpoint (sync version).
        Called by LangGraph's SyncPregelLoop to store intermediate task outputs.
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        project_id = config.get("configurable", {}).get("project_id", "default")
        if thread_id and self.manager and writes:
            _async_runner.run_async(
                self.manager.append_writes(thread_id, task_id, writes)
            )

    async def alist(
        self,
        config: Optional[dict] = None,
        *,
        filter: Optional[dict] = None,
        before: Optional[dict] = None,
        limit: Optional[int] = None,
    ):
        """List checkpoints (not implemented for now)."""
        return
        yield  # Make this an async generator

    async def aput_writes(
        self,
        config: dict,
        writes: list,
        task_id: str,
        task_path: str = "",
    ) -> None:
        """
        Async version of put_writes - called by AsyncPregelLoop.
        Stores intermediate task outputs.
        """
        thread_id = config.get("configurable", {}).get("thread_id")
        project_id = config.get("configurable", {}).get("project_id", "default")
        logger.info(f"[CHECKPOINT aput_writes] thread_id={thread_id}, task_id={task_id}, {len(writes)} writes")
        if thread_id and self.manager and writes:
            await self.manager.append_writes(thread_id, task_id, writes)


# Singleton instance
_session_checkpoint_saver: Optional[SessionCheckpointSaver] = None


def get_session_checkpoint_saver() -> SessionCheckpointSaver:
    """Get singleton SessionCheckpointSaver instance"""
    global _session_checkpoint_saver
    if _session_checkpoint_saver is None:
        _session_checkpoint_saver = SessionCheckpointSaver()
    return _session_checkpoint_saver

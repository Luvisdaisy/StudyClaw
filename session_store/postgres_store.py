"""PostgreSQL session store - backup storage for durability"""

import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class PostgresStore:
    """PostgreSQL-based session storage for durability"""

    def __init__(self, async_session_factory):
        """
        Args:
            async_session_factory: SQLAlchemy async session factory
        """
        self._session_factory = async_session_factory

    async def init_schema(self):
        """Create agent_sessions table if not exists"""
        create_table_sql = text("""
            CREATE TABLE IF NOT EXISTS agent_sessions (
                session_id VARCHAR(255) PRIMARY KEY,
                project_id VARCHAR(255) NOT NULL,
                messages JSONB NOT NULL,
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        create_project_index_sql = text("""
            CREATE INDEX IF NOT EXISTS idx_agent_sessions_project
            ON agent_sessions(project_id)
        """)
        create_updated_index_sql = text("""
            CREATE INDEX IF NOT EXISTS idx_agent_sessions_updated
            ON agent_sessions(updated_at)
        """)

        async with self._session_factory() as session:
            await session.execute(create_table_sql)
            await session.execute(create_project_index_sql)
            await session.execute(create_updated_index_sql)
            await session.commit()
        logger.info("Initialized agent_sessions schema in PostgreSQL")

    async def save(self, session_id: str, project_id: str, messages: list[dict]) -> bool:
        """Save session to PostgreSQL (upsert)"""
        try:
            upsert_sql = text("""
                INSERT INTO agent_sessions (session_id, project_id, messages, updated_at)
                VALUES (:session_id, :project_id, :messages, NOW())
                ON CONFLICT (session_id)
                DO UPDATE SET
                    messages = EXCLUDED.messages,
                    updated_at = NOW()
            """)
            async with self._session_factory() as session:
                await session.execute(
                    upsert_sql,
                    {
                        "session_id": session_id,
                        "project_id": project_id,
                        "messages": json.dumps(messages, ensure_ascii=False),
                    },
                )
                await session.commit()
            logger.debug(f"Saved session {session_id} to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Failed to save session {session_id} to PostgreSQL: {e}")
            return False

    async def load(self, session_id: str) -> Optional[list[dict]]:
        """Load session from PostgreSQL"""
        try:
            select_sql = text("""
                SELECT messages FROM agent_sessions
                WHERE session_id = :session_id
            """)
            async with self._session_factory() as session:
                result = await session.execute(select_sql, {"session_id": session_id})
                row = result.fetchone()
                if row:
                    logger.debug(f"Loaded session {session_id} from PostgreSQL")
                    # asyncpg auto-parses JSONB to Python object
                    messages = row[0]
                    if isinstance(messages, str):
                        return json.loads(messages)
                    return messages
                return None
        except Exception as e:
            logger.error(f"Failed to load session {session_id} from PostgreSQL: {e}")
            return None

    async def delete(self, session_id: str) -> bool:
        """Delete session from PostgreSQL"""
        try:
            delete_sql = text("""
                DELETE FROM agent_sessions WHERE session_id = :session_id
            """)
            async with self._session_factory() as session:
                await session.execute(delete_sql, {"session_id": session_id})
                await session.commit()
            logger.debug(f"Deleted session {session_id} from PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id} from PostgreSQL: {e}")
            return False

    async def load_by_project(self, project_id: str) -> list[dict]:
        """Load all sessions for a project"""
        try:
            select_sql = text("""
                SELECT session_id, messages, updated_at
                FROM agent_sessions
                WHERE project_id = :project_id
                ORDER BY updated_at DESC
                LIMIT 50
            """)
            async with self._session_factory() as session:
                result = await session.execute(select_sql, {"project_id": project_id})
                rows = result.fetchall()
                return [
                    {
                        "session_id": row[0],
                        "messages": json.loads(row[1]) if isinstance(row[1], str) else row[1],
                        "updated_at": row[2].isoformat() if row[2] else None,
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Failed to load sessions for project {project_id}: {e}")
            return []

    async def batch_save(self, sessions: list[dict]) -> bool:
        """Batch save multiple sessions (for periodic sync)"""
        if not sessions:
            return True
        try:
            insert_sql = text("""
                INSERT INTO agent_sessions (session_id, project_id, messages, updated_at)
                VALUES (:session_id, :project_id, :messages, NOW())
                ON CONFLICT (session_id)
                DO UPDATE SET
                    messages = EXCLUDED.messages,
                    updated_at = NOW()
            """)
            async with self._session_factory() as session:
                for s in sessions:
                    await session.execute(
                        insert_sql,
                        {
                            "session_id": s["session_id"],
                            "project_id": s["project_id"],
                            "messages": json.dumps(s["messages"], ensure_ascii=False),
                        },
                    )
                await session.commit()
            logger.info(f"Batch saved {len(sessions)} sessions to PostgreSQL")
            return True
        except Exception as e:
            logger.error(f"Failed to batch save sessions to PostgreSQL: {e}")
            return False

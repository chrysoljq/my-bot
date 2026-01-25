
from typing import List, Dict, Any
import time
from nonebot import logger
from ..datastore import db

async def init_db():
    try:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS ai_chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                nick_name TEXT NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp INTEGER NOT NULL
            )
        """)
        # Index for faster retrieval by group
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_ai_chat_messages_group_timestamp 
            ON ai_chat_messages (group_id, timestamp DESC)
        """)
    except Exception as e:
        logger.error(f"Failed to initialize ai_chat database: {e}")

async def save_message(group_id: int, nick_name: str, user_id: int, role: str, content: str, timestamp: int):
    try:
        current_time = int(time.time()) if timestamp is None else timestamp
        await db.execute(
            """
            INSERT INTO ai_chat_messages (group_id, nick_name, user_id, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (group_id, nick_name, user_id, role, content, current_time)
        )
    except Exception as e:
        logger.error(f"Failed to save ai_chat message: {e}")

async def get_chat_history(group_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    try:
        rows = await db.fetchall(
            """
            SELECT nick_name, user_id, role, content, timestamp 
            FROM ai_chat_messages 
            WHERE group_id = ? 
            ORDER BY timestamp DESC 
            LIMIT ?
            """,
            (group_id, limit)
        )
        # Reverse to get chronological order for the prompt
        return sorted([dict(row) for row in rows], key=lambda x: x['timestamp'])
    except Exception as e:
        logger.error(f"Failed to fetch ai_chat history: {e}")
        return []

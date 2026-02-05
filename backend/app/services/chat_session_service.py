"""聊天會話服務層"""
from datetime import datetime
from typing import Optional, List
from pymongo.asynchronous.database import AsyncDatabase

from ..models.chat_session import ChatSession


class ChatSessionService:
    """聊天會話服務"""

    def __init__(self, db: AsyncDatabase):
        self.db = db
        self.collection = db.chat_sessions

    async def get_session(self, project_id: str, thread_id: str) -> Optional[ChatSession]:
        """取得單一聊天會話"""
        session = await self.collection.find_one(
            {"project_id": project_id, "thread_id": thread_id}
        )
        if not session:
            return None
        session["_id"] = str(session["_id"])
        return ChatSession(**session)

    async def list_sessions(
        self, project_id: str, limit: int = 100
    ) -> List[ChatSession]:
        """列出專案的聊天會話（依最後訊息時間排序）"""
        cursor = (
            self.collection.find({"project_id": project_id})
            .sort("last_message_at", -1)
            .limit(limit)
        )
        sessions: List[ChatSession] = []
        async for session in cursor:
            session["_id"] = str(session["_id"])
            sessions.append(ChatSession(**session))
        return sessions

    async def upsert_session(
        self,
        project_id: str,
        thread_id: str,
        title: Optional[str] = None,
    ) -> ChatSession:
        """建立或更新聊天會話（更新最後訊息時間）"""
        now = datetime.utcnow()
        update = {
            "$set": {"last_message_at": now},
            "$setOnInsert": {
                "project_id": project_id,
                "thread_id": thread_id,
                "title": title,
                "created_at": now,
            },
        }
        await self.collection.update_one(
            {"project_id": project_id, "thread_id": thread_id},
            update,
            upsert=True,
        )
        return await self.get_session(project_id, thread_id)

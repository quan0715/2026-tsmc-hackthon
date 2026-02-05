"""Chat Session Service 單元測試"""
import pytest
from app.services.chat_session_service import ChatSessionService
from datetime import datetime


class TestChatSessionService:
    """聊天會話服務測試"""

    @pytest.mark.asyncio
    async def test_create_session(self, chat_session_service: ChatSessionService):
        """測試建立會話"""
        project_id = "test-project-1"
        thread_id = "thread-123"
        title = "Test conversation"

        session = await chat_session_service.upsert_session(
            project_id=project_id,
            thread_id=thread_id,
            title=title
        )

        assert session is not None
        assert session.project_id == project_id
        assert session.thread_id == thread_id
        assert session.title == title
        assert session.created_at is not None
        assert session.last_message_at is not None

    @pytest.mark.asyncio
    async def test_get_session(self, chat_session_service: ChatSessionService):
        """測試查詢會話"""
        project_id = "test-project-1"
        thread_id = "thread-123"

        # 先建立會話
        await chat_session_service.upsert_session(
            project_id=project_id,
            thread_id=thread_id,
            title="Test"
        )

        # 查詢會話
        session = await chat_session_service.get_session(project_id, thread_id)

        assert session is not None
        assert session.project_id == project_id
        assert session.thread_id == thread_id

    @pytest.mark.asyncio
    async def test_list_sessions(self, chat_session_service: ChatSessionService):
        """測試列出專案會話"""
        project_id = "test-project-1"

        # 建立多個會話
        await chat_session_service.upsert_session(project_id, "thread-1", "Session 1")
        await chat_session_service.upsert_session(project_id, "thread-2", "Session 2")
        await chat_session_service.upsert_session(project_id, "thread-3", "Session 3")

        # 列出會話
        sessions = await chat_session_service.list_sessions(project_id)

        assert len(sessions) == 3
        # 確認按時間排序（最新的在前）
        assert sessions[0].last_message_at >= sessions[1].last_message_at
        assert sessions[1].last_message_at >= sessions[2].last_message_at

    @pytest.mark.asyncio
    async def test_upsert_session_create(self, chat_session_service: ChatSessionService):
        """測試 upsert - 首次建立"""
        project_id = "test-project-1"
        thread_id = "thread-new"

        session = await chat_session_service.upsert_session(
            project_id=project_id,
            thread_id=thread_id,
            title="New Session"
        )

        assert session.title == "New Session"
        assert session.created_at is not None

    @pytest.mark.asyncio
    async def test_upsert_session_update(self, chat_session_service: ChatSessionService):
        """測試 upsert - 更新最後訊息時間"""
        project_id = "test-project-1"
        thread_id = "thread-existing"

        # 首次建立
        session1 = await chat_session_service.upsert_session(
            project_id=project_id,
            thread_id=thread_id,
            title="Original Title"
        )
        first_time = session1.last_message_at

        # 等待一下
        import asyncio
        await asyncio.sleep(0.1)

        # 再次 upsert（更新時間）
        session2 = await chat_session_service.upsert_session(
            project_id=project_id,
            thread_id=thread_id
        )

        # 標題應該保持原樣（因為 $setOnInsert）
        assert session2.title == "Original Title"
        # 最後訊息時間應該更新
        assert session2.last_message_at > first_time
        # created_at 應該不變
        assert session2.created_at == session1.created_at

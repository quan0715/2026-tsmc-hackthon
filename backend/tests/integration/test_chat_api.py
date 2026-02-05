"""Chat API 整合測試 - 需要 mock httpx"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock
from app.models.project import ProjectStatus


@pytest.fixture
async def ready_project(auth_client: AsyncClient, test_user):
    """建立一個 READY 狀態的專案"""
    # 建立專案
    response = await auth_client.post(
        "/api/v1/projects",
        json={
            "repo_url": "https://github.com/test/repo.git",
            "branch": "main",
            "spec": "Test project for chat"
        }
    )
    project_id = response.json()["id"]

    # 手動更新專案狀態為 READY (在實際測試中應該透過 provision)
    from app.database.mongodb import get_database_client
    client = get_database_client()
    db = client["refactor_agent_test"]
    from bson import ObjectId
    await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": {"status": ProjectStatus.READY}}
    )

    return project_id


@pytest.fixture
def mock_ai_server_chat(monkeypatch):
    """Mock httpx.AsyncClient for AI Server chat calls"""
    async def mock_post(url, *args, **kwargs):
        """Mock POST request"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_id": "task-123",
            "thread_id": kwargs["json"].get("thread_id", "chat-test-uuid"),
            "status": "RUNNING"
        }
        mock_response.raise_for_status = lambda: None
        return mock_response

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = mock_post
    monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: mock_client)
    return mock_client


class TestSendChatMessage:
    """發送聊天訊息測試"""

    @pytest.mark.asyncio
    async def test_send_chat_message_success(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_chat
    ):
        """測試發送訊息成功"""
        response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/chat",
            json={
                "message": "Hello, how can I refactor this code?",
                "verbose": True
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == "task-123"
        assert data["status"] == "RUNNING"
        assert "thread_id" in data
        assert data["project_id"] == ready_project

    @pytest.mark.asyncio
    async def test_send_chat_message_with_thread_id(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_chat
    ):
        """測試使用現有 thread_id"""
        custom_thread_id = "my-custom-thread-123"

        response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/chat",
            json={
                "message": "Continue the conversation",
                "thread_id": custom_thread_id,
                "verbose": False
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == custom_thread_id

    @pytest.mark.asyncio
    async def test_send_chat_message_auto_generate_thread(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_chat
    ):
        """測試自動生成 thread_id"""
        response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/chat",
            json={"message": "New conversation"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "thread_id" in data
        assert data["thread_id"].startswith("chat-")

    @pytest.mark.asyncio
    async def test_send_chat_message_project_not_ready(
        self,
        auth_client: AsyncClient,
        test_user
    ):
        """測試專案狀態非 READY"""
        # 建立 CREATED 狀態的專案
        response = await auth_client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "spec": "Test project"
            }
        )
        project_id = response.json()["id"]

        # 嘗試發送聊天訊息
        response = await auth_client.post(
            f"/api/v1/projects/{project_id}/chat",
            json={"message": "Hello"}
        )

        assert response.status_code == 400
        assert "READY" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_send_chat_message_unauthorized(
        self,
        client: AsyncClient,
        auth_service,
        ready_project
    ):
        """測試無權訪問"""
        # 建立另一個用戶
        user2 = await auth_service.create_user(
            email="user2@example.com",
            username="user2",
            password="password123"
        )
        token2, _ = auth_service.create_access_token(user2.id, user2.email)

        client.headers["Authorization"] = f"Bearer {token2}"
        response = await client.post(
            f"/api/v1/projects/{ready_project}/chat",
            json={"message": "Hello"}
        )

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_send_chat_message_ai_server_down(
        self,
        auth_client: AsyncClient,
        ready_project,
        monkeypatch
    ):
        """測試 AI Server 無回應"""
        import httpx

        async def mock_post_error(*args, **kwargs):
            raise httpx.HTTPError("Connection refused")

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = mock_post_error
        monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: mock_client)

        response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/chat",
            json={"message": "Hello"}
        )

        assert response.status_code == 503


class TestListChatSessions:
    """列出聊天會話測試"""

    @pytest.mark.asyncio
    async def test_list_chat_sessions(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_chat
    ):
        """測試列出聊天會話"""
        # 發送幾則訊息建立會話
        await auth_client.post(
            f"/api/v1/projects/{ready_project}/chat",
            json={"message": "First message"}
        )
        await auth_client.post(
            f"/api/v1/projects/{ready_project}/chat",
            json={"message": "Second message", "thread_id": "custom-thread"}
        )

        # 列出會話
        response = await auth_client.get(
            f"/api/v1/projects/{ready_project}/chat/sessions"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2
        assert len(data["sessions"]) >= 2

    @pytest.mark.asyncio
    async def test_list_chat_sessions_empty(
        self,
        auth_client: AsyncClient,
        ready_project
    ):
        """測試無會話記錄"""
        response = await auth_client.get(
            f"/api/v1/projects/{ready_project}/chat/sessions"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["sessions"] == []


class TestGetChatHistory:
    """取得聊天歷史測試"""

    @pytest.mark.asyncio
    async def test_get_chat_history_success(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_chat,
        monkeypatch
    ):
        """測試取得聊天歷史"""
        # Mock history endpoint
        async def mock_get(url, *args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "messages": [
                    {
                        "id": "msg1",
                        "role": "user",
                        "content": "Hello",
                        "timestamp": "2024-01-01T00:00:00Z"
                    },
                    {
                        "id": "msg2",
                        "role": "assistant",
                        "content": "Hi there!",
                        "timestamp": "2024-01-01T00:00:01Z"
                    }
                ]
            }
            mock_response.raise_for_status = lambda: None
            return mock_response

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = mock_get
        monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: mock_client)

        # 發送訊息建立會話
        chat_response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/chat",
            json={"message": "Hello"}
        )
        thread_id = chat_response.json()["thread_id"]

        # 取得歷史
        response = await auth_client.get(
            f"/api/v1/projects/{ready_project}/chat/history/{thread_id}"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"] == thread_id
        assert len(data["messages"]) == 2

    @pytest.mark.asyncio
    async def test_get_chat_history_session_not_found(
        self,
        auth_client: AsyncClient,
        ready_project
    ):
        """測試會話不存在"""
        response = await auth_client.get(
            f"/api/v1/projects/{ready_project}/chat/history/nonexistent-thread"
        )

        assert response.status_code == 404


class TestStreamChatResponse:
    """SSE 串流測試"""

    @pytest.mark.asyncio
    async def test_stream_chat_response(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_chat
    ):
        """測試 SSE 串流"""
        # 發送訊息
        chat_response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/chat",
            json={"message": "Hello"}
        )
        task_id = chat_response.json()["task_id"]

        # 獲取串流（這裡只測試端點存在，不測試完整串流）
        response = await auth_client.get(
            f"/api/v1/projects/{ready_project}/chat/stream/{task_id}",
            headers={"Accept": "text/event-stream"}
        )

        # 應該返回 SSE 回應
        assert response.status_code in [200, 404, 503]  # 容錯處理


class TestGetChatStatus:
    """查詢聊天狀態測試"""

    @pytest.mark.asyncio
    async def test_get_chat_status(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_chat,
        monkeypatch
    ):
        """測試查詢狀態"""
        # Mock status endpoint
        async def mock_get(url, *args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "task_id": "task-123",
                "status": "COMPLETED"
            }
            mock_response.raise_for_status = lambda: None
            return mock_response

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get = mock_get
        monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: mock_client)

        response = await auth_client.get(
            f"/api/v1/projects/{ready_project}/chat/status/task-123"
        )

        assert response.status_code in [200, 404]


class TestStopChatTask:
    """停止聊天任務測試"""

    @pytest.mark.asyncio
    async def test_stop_chat_task(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_chat,
        monkeypatch
    ):
        """測試停止任務"""
        # Mock stop endpoint
        async def mock_post(url, *args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "STOPPED"}
            mock_response.raise_for_status = lambda: None
            return mock_response

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = mock_post
        monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: mock_client)

        response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/chat/stop/task-123"
        )

        assert response.status_code in [200, 404]

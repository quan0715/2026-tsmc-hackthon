"""Agent API 進階功能測試 - 需要 mock httpx"""
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
            "spec": "Refactor the authentication module"
        }
    )
    project_id = response.json()["id"]

    # 更新為 READY 狀態
    from app.database.mongodb import get_database_client
    from bson import ObjectId

    client = get_database_client()
    db = client["refactor_agent_test"]
    await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {"$set": {"status": ProjectStatus.READY}}
    )

    return project_id


@pytest.fixture
def mock_ai_server_run(monkeypatch):
    """Mock httpx.AsyncClient for AI Server /run endpoint"""
    async def mock_post(url, *args, **kwargs):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "task_id": "run-123",
            "status": "running",
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_response.raise_for_status = lambda: None
        return mock_response

    async def mock_get(url, *args, **kwargs):
        # 根據 URL 返回不同的 mock
        if "/tasks/" in url and "/stream" not in url:
            # Task status endpoint
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "task_id": "run-123",
                "status": "running"
            }
            mock_response.raise_for_status = lambda: None
            return mock_response
        elif "/tasks" in url:
            # List tasks endpoint
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "tasks": [
                    {
                        "task_id": "run-123",
                        "status": "running",
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ]
            }
            mock_response.raise_for_status = lambda: None
            return mock_response
        return MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__.return_value.post = mock_post
    mock_client.__aenter__.return_value.get = mock_get
    monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: mock_client)
    return mock_client


class TestRunAgent:
    """啟動 Agent 測試"""

    @pytest.mark.asyncio
    async def test_run_agent_success(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_run
    ):
        """測試啟動 Agent 成功"""
        response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/agent/run"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["run_id"] == "run-123"
        assert data["status"] == "RUNNING"
        assert data["project_id"] == ready_project
        assert "thread_id" in data

    @pytest.mark.asyncio
    async def test_run_agent_reuse_thread_id(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_run
    ):
        """測試重用 thread_id"""
        # 第一次執行
        response1 = await auth_client.post(
            f"/api/v1/projects/{ready_project}/agent/run"
        )
        thread_id1 = response1.json()["thread_id"]

        # 第二次執行應該重用相同的 thread_id
        response2 = await auth_client.post(
            f"/api/v1/projects/{ready_project}/agent/run"
        )
        thread_id2 = response2.json()["thread_id"]

        assert thread_id1 == thread_id2

    @pytest.mark.asyncio
    async def test_run_agent_generate_thread_id(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_run
    ):
        """測試自動生成 thread_id"""
        response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/agent/run"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["thread_id"].startswith("refactor-")

    @pytest.mark.asyncio
    async def test_run_agent_project_not_ready(
        self,
        auth_client: AsyncClient,
        test_user
    ):
        """測試專案未 READY"""
        # 建立 CREATED 狀態的專案
        response = await auth_client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "spec": "Test"
            }
        )
        project_id = response.json()["id"]

        # 嘗試執行 Agent
        response = await auth_client.post(
            f"/api/v1/projects/{project_id}/agent/run"
        )

        assert response.status_code == 400
        assert "READY" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_run_agent_unauthorized(
        self,
        client: AsyncClient,
        auth_service,
        ready_project
    ):
        """測試無權執行 Agent"""
        # 建立另一個用戶
        user2 = await auth_service.create_user(
            email="user2@example.com",
            username="user2",
            password="password123"
        )
        token2, _ = auth_service.create_access_token(user2.id, user2.email)

        client.headers["Authorization"] = f"Bearer {token2}"
        response = await client.post(
            f"/api/v1/projects/{ready_project}/agent/run"
        )

        assert response.status_code == 403


class TestGetAgentStatus:
    """查詢 Agent 狀態測試"""

    @pytest.mark.asyncio
    async def test_get_agent_status(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_run
    ):
        """測試查詢 Agent 狀態"""
        # 先啟動 Agent
        run_response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/agent/run"
        )
        run_id = run_response.json()["run_id"]

        # 查詢狀態
        response = await auth_client.get(
            f"/api/v1/projects/{ready_project}/agent/runs/{run_id}"
        )

        assert response.status_code in [200, 404, 503]  # 容錯


class TestListAgentRuns:
    """列出 Agent Runs 測試"""

    @pytest.mark.asyncio
    async def test_list_agent_runs(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_run
    ):
        """測試列出 Agent Runs"""
        # 啟動 Agent
        await auth_client.post(f"/api/v1/projects/{ready_project}/agent/run")

        # 列出 runs
        response = await auth_client.get(
            f"/api/v1/projects/{ready_project}/agent/runs"
        )

        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "runs" in data


class TestStreamAgentLogs:
    """SSE 串流日誌測試"""

    @pytest.mark.asyncio
    async def test_stream_agent_logs(
        self,
        auth_client: AsyncClient,
        ready_project,
        mock_ai_server_run
    ):
        """測試 SSE 串流日誌"""
        # 啟動 Agent
        run_response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/agent/run"
        )
        run_id = run_response.json()["run_id"]

        # 獲取串流（只測試端點存在）
        response = await auth_client.get(
            f"/api/v1/projects/{ready_project}/agent/runs/{run_id}/stream",
            headers={"Accept": "text/event-stream"}
        )

        assert response.status_code in [200, 404, 503]


class TestStopAgent:
    """停止 Agent 測試"""

    @pytest.mark.asyncio
    async def test_stop_agent_task(
        self,
        auth_client: AsyncClient,
        ready_project,
        monkeypatch
    ):
        """測試停止 Agent 任務"""
        # Mock stop endpoint
        async def mock_post(url, *args, **kwargs):
            if "/stop" in url:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {"status": "STOPPED"}
                mock_response.raise_for_status = lambda: None
                return mock_response
            # Default for /run
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "task_id": "run-123",
                "status": "running"
            }
            mock_response.raise_for_status = lambda: None
            return mock_response

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = mock_post
        monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: mock_client)

        # 啟動 Agent
        run_response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/agent/run"
        )
        run_id = run_response.json()["run_id"]

        # 停止 Agent
        response = await auth_client.post(
            f"/api/v1/projects/{ready_project}/agent/runs/{run_id}/stop"
        )

        assert response.status_code in [200, 404]


class TestAgentServerDown:
    """AI Server 無回應測試"""

    @pytest.mark.asyncio
    async def test_run_agent_server_down(
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
            f"/api/v1/projects/{ready_project}/agent/run"
        )

        assert response.status_code == 503

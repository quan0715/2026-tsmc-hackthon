"""端到端流程測試"""
import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock
from app.models.project import ProjectStatus
import asyncio


class TestFullChatWorkflow:
    """完整聊天流程測試"""

    @pytest.mark.asyncio
    async def test_full_chat_workflow(
        self,
        auth_client: AsyncClient,
        test_user,
        monkeypatch
    ):
        """測試完整聊天流程：註冊→建立專案→Provision→聊天→查詢歷史"""

        # Mock AI Server
        async def mock_post(url, *args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            if "/chat" in url:
                mock_response.json.return_value = {
                    "task_id": "chat-task-1",
                    "thread_id": kwargs["json"].get("thread_id", "thread-1"),
                    "status": "RUNNING"
                }
            mock_response.raise_for_status = lambda: None
            return mock_response

        async def mock_get(url, *args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            if "/history" in url:
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
                            "content": "Hi!",
                            "timestamp": "2024-01-01T00:00:01Z"
                        }
                    ]
                }
            mock_response.raise_for_status = lambda: None
            return mock_response

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = mock_post
        mock_client.__aenter__.return_value.get = mock_get
        monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: mock_client)

        # Step 1: 建立專案
        create_response = await auth_client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "spec": "Test project"
            }
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]

        # Step 2: 手動設定為 READY (模擬 Provision)
        from app.database.mongodb import get_database_client
        from bson import ObjectId

        client = get_database_client()
        db = client["refactor_agent_test"]
        await db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": ProjectStatus.READY}}
        )

        # Step 3: 發送聊天訊息
        chat_response = await auth_client.post(
            f"/api/v1/projects/{project_id}/chat",
            json={"message": "Hello, how are you?"}
        )
        assert chat_response.status_code == 200
        thread_id = chat_response.json()["thread_id"]

        # Step 4: 列出會話
        sessions_response = await auth_client.get(
            f"/api/v1/projects/{project_id}/chat/sessions"
        )
        assert sessions_response.status_code == 200
        assert sessions_response.json()["total"] >= 1

        # Step 5: 查詢聊天歷史
        history_response = await auth_client.get(
            f"/api/v1/projects/{project_id}/chat/history/{thread_id}"
        )
        assert history_response.status_code == 200
        messages = history_response.json()["messages"]
        assert len(messages) == 2


class TestFullAgentWorkflowWithResume:
    """Agent 執行與恢復測試"""

    @pytest.mark.asyncio
    async def test_full_agent_workflow_with_resume(
        self,
        auth_client: AsyncClient,
        test_user,
        monkeypatch
    ):
        """測試完整 Agent 流程：建立專案→執行 Agent→查詢狀態→重複執行"""

        # Mock AI Server
        task_counter = {"count": 0}

        async def mock_post(url, *args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            task_counter["count"] += 1
            mock_response.json.return_value = {
                "task_id": f"agent-task-{task_counter['count']}",
                "status": "running",
                "created_at": "2024-01-01T00:00:00Z"
            }
            mock_response.raise_for_status = lambda: None
            return mock_response

        async def mock_get(url, *args, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            if "/tasks/" in url:
                mock_response.json.return_value = {
                    "task_id": "agent-task-1",
                    "status": "success"
                }
            elif "/tasks" in url:
                mock_response.json.return_value = {
                    "tasks": [
                        {"task_id": f"agent-task-{i}", "status": "success"}
                        for i in range(1, task_counter["count"] + 1)
                    ]
                }
            mock_response.raise_for_status = lambda: None
            return mock_response

        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post = mock_post
        mock_client.__aenter__.return_value.get = mock_get
        monkeypatch.setattr("httpx.AsyncClient", lambda *args, **kwargs: mock_client)

        # Step 1: 建立並設定專案
        create_response = await auth_client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "spec": "Refactor authentication"
            }
        )
        project_id = create_response.json()["id"]

        from app.database.mongodb import get_database_client
        from bson import ObjectId

        client = get_database_client()
        db = client["refactor_agent_test"]
        await db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": ProjectStatus.READY}}
        )

        # Step 2: 第一次執行 Agent
        run1_response = await auth_client.post(
            f"/api/v1/projects/{project_id}/agent/run"
        )
        assert run1_response.status_code == 200
        run1_id = run1_response.json()["run_id"]
        thread_id = run1_response.json()["thread_id"]

        # Step 3: 查詢狀態
        status_response = await auth_client.get(
            f"/api/v1/projects/{project_id}/agent/runs/{run1_id}"
        )
        assert status_response.status_code in [200, 404]

        # Step 4: 第二次執行（應該重用 thread_id）
        run2_response = await auth_client.post(
            f"/api/v1/projects/{project_id}/agent/run"
        )
        assert run2_response.status_code == 200
        assert run2_response.json()["thread_id"] == thread_id

        # Step 5: 列出所有 runs
        runs_response = await auth_client.get(
            f"/api/v1/projects/{project_id}/agent/runs"
        )
        assert runs_response.status_code == 200
        assert runs_response.json()["total"] >= 2


class TestMultiUserConcurrentAccess:
    """多用戶並發訪問測試"""

    @pytest.mark.asyncio
    async def test_multi_user_concurrent_access(
        self,
        client: AsyncClient,
        auth_service
    ):
        """測試多用戶並發建立和訪問專案"""

        # 建立兩個用戶
        user1 = await auth_service.create_user(
            email="user1@example.com",
            username="user1",
            password="password123"
        )
        user2 = await auth_service.create_user(
            email="user2@example.com",
            username="user2",
            password="password123"
        )

        token1, _ = auth_service.create_access_token(user1.id, user1.email)
        token2, _ = auth_service.create_access_token(user2.id, user2.email)

        # 並發建立專案
        async def create_projects_for_user(token, user_num):
            client_headers = {"Authorization": f"Bearer {token}"}
            projects = []
            for i in range(3):
                response = await client.post(
                    "/api/v1/projects",
                    json={
                        "repo_url": f"https://github.com/user{user_num}/repo{i}.git",
                        "branch": "main",
                        "spec": f"User {user_num} project {i}"
                    },
                    headers=client_headers
                )
                assert response.status_code == 201
                projects.append(response.json()["id"])
            return projects

        # 並發執行
        user1_projects, user2_projects = await asyncio.gather(
            create_projects_for_user(token1, 1),
            create_projects_for_user(token2, 2)
        )

        # 驗證：每個用戶只能看到自己的專案
        client.headers = {"Authorization": f"Bearer {token1}"}
        response1 = await client.get("/api/v1/projects")
        assert response1.status_code == 200
        user1_list = response1.json()["projects"]
        assert len(user1_list) == 3
        assert all(p["id"] in user1_projects for p in user1_list)

        client.headers = {"Authorization": f"Bearer {token2}"}
        response2 = await client.get("/api/v1/projects")
        assert response2.status_code == 200
        user2_list = response2.json()["projects"]
        assert len(user2_list) == 3
        assert all(p["id"] in user2_projects for p in user2_list)

        # 驗證：用戶無法訪問他人專案
        client.headers = {"Authorization": f"Bearer {token1}"}
        for project_id in user2_projects:
            response = await client.get(f"/api/v1/projects/{project_id}")
            assert response.status_code == 403

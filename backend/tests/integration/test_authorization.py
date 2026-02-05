"""Authorization 測試 - 測試專案權限控制"""
import pytest
from httpx import AsyncClient
from app.services.auth_service import AuthService


class TestProjectAuthorization:
    """專案授權測試"""

    @pytest.mark.asyncio
    async def test_access_other_user_project(
        self,
        client: AsyncClient,
        auth_service: AuthService,
        project_factory
    ):
        """測試無權訪問他人專案"""
        # 建立第一個用戶和他的專案
        user1 = await auth_service.create_user(
            email="user1@example.com",
            username="user1",
            password="password123"
        )
        token1, _ = auth_service.create_access_token(user1.id, user1.email)

        # 建立專案
        client.headers["Authorization"] = f"Bearer {token1}"
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/user/repo.git",
                "branch": "main",
                "spec": "User1's project"
            }
        )
        project_id = create_response.json()["id"]

        # 建立第二個用戶
        user2 = await auth_service.create_user(
            email="user2@example.com",
            username="user2",
            password="password123"
        )
        token2, _ = auth_service.create_access_token(user2.id, user2.email)

        # 第二個用戶嘗試訪問第一個用戶的專案
        client.headers["Authorization"] = f"Bearer {token2}"
        response = await client.get(f"/api/v1/projects/{project_id}")

        assert response.status_code == 403
        assert "無權限訪問此專案" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_other_user_project(
        self,
        client: AsyncClient,
        auth_service: AuthService
    ):
        """測試無權更新他人專案"""
        # 建立第一個用戶和專案
        user1 = await auth_service.create_user(
            email="user1@example.com",
            username="user1",
            password="password123"
        )
        token1, _ = auth_service.create_access_token(user1.id, user1.email)

        client.headers["Authorization"] = f"Bearer {token1}"
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/user/repo.git",
                "branch": "main",
                "spec": "User1's project"
            }
        )
        project_id = create_response.json()["id"]

        # 建立第二個用戶
        user2 = await auth_service.create_user(
            email="user2@example.com",
            username="user2",
            password="password123"
        )
        token2, _ = auth_service.create_access_token(user2.id, user2.email)

        # 第二個用戶嘗試更新第一個用戶的專案
        client.headers["Authorization"] = f"Bearer {token2}"
        response = await client.put(
            f"/api/v1/projects/{project_id}",
            json={"spec": "Modified by user2"}
        )

        assert response.status_code == 403
        assert "無權限訪問此專案" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_other_user_project(
        self,
        client: AsyncClient,
        auth_service: AuthService
    ):
        """測試無權刪除他人專案"""
        # 建立第一個用戶和專案
        user1 = await auth_service.create_user(
            email="user1@example.com",
            username="user1",
            password="password123"
        )
        token1, _ = auth_service.create_access_token(user1.id, user1.email)

        client.headers["Authorization"] = f"Bearer {token1}"
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/user/repo.git",
                "branch": "main",
                "spec": "User1's project"
            }
        )
        project_id = create_response.json()["id"]

        # 建立第二個用戶
        user2 = await auth_service.create_user(
            email="user2@example.com",
            username="user2",
            password="password123"
        )
        token2, _ = auth_service.create_access_token(user2.id, user2.email)

        # 第二個用戶嘗試刪除第一個用戶的專案
        client.headers["Authorization"] = f"Bearer {token2}"
        response = await client.delete(f"/api/v1/projects/{project_id}")

        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_list_projects_only_own(
        self,
        client: AsyncClient,
        auth_service: AuthService
    ):
        """測試只列出自己的專案"""
        # 建立第一個用戶和專案
        user1 = await auth_service.create_user(
            email="user1@example.com",
            username="user1",
            password="password123"
        )
        token1, _ = auth_service.create_access_token(user1.id, user1.email)

        client.headers["Authorization"] = f"Bearer {token1}"
        await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/user1/repo1.git",
                "branch": "main",
                "spec": "User1's project 1"
            }
        )
        await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/user1/repo2.git",
                "branch": "main",
                "spec": "User1's project 2"
            }
        )

        # 建立第二個用戶和專案
        user2 = await auth_service.create_user(
            email="user2@example.com",
            username="user2",
            password="password123"
        )
        token2, _ = auth_service.create_access_token(user2.id, user2.email)

        client.headers["Authorization"] = f"Bearer {token2}"
        await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/user2/repo.git",
                "branch": "main",
                "spec": "User2's project"
            }
        )

        # 第二個用戶列出專案，應該只看到自己的專案
        response = await client.get("/api/v1/projects")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["projects"]) == 1
        assert data["projects"][0]["spec"] == "User2's project"

    @pytest.mark.asyncio
    async def test_agent_run_unauthorized_project(
        self,
        client: AsyncClient,
        auth_service: AuthService
    ):
        """測試無權在他人專案執行 Agent"""
        # 建立第一個用戶和專案
        user1 = await auth_service.create_user(
            email="user1@example.com",
            username="user1",
            password="password123"
        )
        token1, _ = auth_service.create_access_token(user1.id, user1.email)

        client.headers["Authorization"] = f"Bearer {token1}"
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/user/repo.git",
                "branch": "main",
                "spec": "User1's project"
            }
        )
        project_id = create_response.json()["id"]

        # 建立第二個用戶
        user2 = await auth_service.create_user(
            email="user2@example.com",
            username="user2",
            password="password123"
        )
        token2, _ = auth_service.create_access_token(user2.id, user2.email)

        # 第二個用戶嘗試在第一個用戶的專案執行 Agent
        client.headers["Authorization"] = f"Bearer {token2}"
        response = await client.post(
            f"/api/v1/projects/{project_id}/agent/run",
            json={"prompt": "Test prompt"}
        )

        assert response.status_code == 403

"""Project Update API 測試"""
import pytest
from httpx import AsyncClient
from app.models.project import ProjectStatus


class TestProjectUpdate:
    """專案更新測試"""

    @pytest.mark.asyncio
    async def test_update_project_title(self, auth_client: AsyncClient):
        """測試更新標題"""
        # 建立專案
        create_response = await auth_client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "spec": "Original spec"
            }
        )
        project_id = create_response.json()["id"]

        # 更新標題
        response = await auth_client.put(
            f"/api/v1/projects/{project_id}",
            json={"title": "Updated Title"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_project_description(self, auth_client: AsyncClient):
        """測試更新描述"""
        # 建立專案
        create_response = await auth_client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "spec": "Original spec"
            }
        )
        project_id = create_response.json()["id"]

        # 更新描述
        response = await auth_client.put(
            f"/api/v1/projects/{project_id}",
            json={"description": "Updated description"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_update_project_spec(self, auth_client: AsyncClient):
        """測試更新 spec"""
        # 建立專案
        create_response = await auth_client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "spec": "Original spec"
            }
        )
        project_id = create_response.json()["id"]

        # 更新 spec
        response = await auth_client.put(
            f"/api/v1/projects/{project_id}",
            json={"spec": "Updated spec content"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["spec"] == "Updated spec content"

    @pytest.mark.asyncio
    async def test_update_project_repo_url_before_provision(self, auth_client: AsyncClient):
        """測試 Provision 前可更新 repo_url"""
        # 建立專案（狀態為 CREATED）
        create_response = await auth_client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "spec": "Test"
            }
        )
        project_id = create_response.json()["id"]

        # 更新 repo_url
        response = await auth_client.put(
            f"/api/v1/projects/{project_id}",
            json={"repo_url": "https://github.com/test/new-repo.git"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["repo_url"] == "https://github.com/test/new-repo.git"

    @pytest.mark.asyncio
    async def test_update_project_repo_url_after_provision(self, auth_client: AsyncClient):
        """測試 Provision 後不可更新 repo_url"""
        # 建立專案
        create_response = await auth_client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "spec": "Test"
            }
        )
        project_id = create_response.json()["id"]

        # 手動更新專案狀態為 READY（模擬已 provision）
        from app.database.mongodb import get_database_client
        from bson import ObjectId

        client = get_database_client()
        db = client["refactor_agent_test"]
        await db.projects.update_one(
            {"_id": ObjectId(project_id)},
            {"$set": {"status": ProjectStatus.READY}}
        )

        # 嘗試更新 repo_url
        response = await auth_client.put(
            f"/api/v1/projects/{project_id}",
            json={"repo_url": "https://github.com/test/new-repo.git"}
        )

        assert response.status_code == 400
        assert "Provision" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_nonexistent_project(self, auth_client: AsyncClient):
        """測試更新不存在的專案"""
        response = await auth_client.put(
            "/api/v1/projects/507f1f77bcf86cd799439011",
            json={"title": "New Title"}
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_unauthorized_project(
        self,
        client: AsyncClient,
        auth_service
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
                "repo_url": "https://github.com/test/repo.git",
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
            json={"title": "Hacked Title"}
        )

        assert response.status_code == 403


class TestProjectMultipleFieldsUpdate:
    """測試同時更新多個欄位"""

    @pytest.mark.asyncio
    async def test_update_multiple_fields(self, auth_client: AsyncClient):
        """測試同時更新多個欄位"""
        # 建立專案
        create_response = await auth_client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "spec": "Original spec"
            }
        )
        project_id = create_response.json()["id"]

        # 同時更新多個欄位
        response = await auth_client.put(
            f"/api/v1/projects/{project_id}",
            json={
                "title": "New Title",
                "description": "New Description",
                "spec": "New Spec"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Title"
        assert data["description"] == "New Description"
        assert data["spec"] == "New Spec"

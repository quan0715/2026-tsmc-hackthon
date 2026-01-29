"""專案 API 測試"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_create_project():
    """測試建立專案"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/user/repo.git",
                "branch": "main",
                "init_prompt": "Test project",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["repo_url"] == "https://github.com/user/repo.git"
        assert data["branch"] == "main"
        assert data["status"] == "CREATED"
        assert data["container_id"] is None


@pytest.mark.asyncio
async def test_get_project():
    """測試查詢專案"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先建立專案
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/user/repo.git",
                "branch": "main",
                "init_prompt": "Test project",
            },
        )
        project_id = create_response.json()["id"]

        # 查詢專案
        response = await client.get(f"/api/v1/projects/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == project_id
        assert data["repo_url"] == "https://github.com/user/repo.git"


@pytest.mark.asyncio
async def test_get_nonexistent_project():
    """測試查詢不存在的專案"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/projects/507f1f77bcf86cd799439011")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_projects():
    """測試列出專案"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 建立幾個專案
        for i in range(3):
            await client.post(
                "/api/v1/projects",
                json={
                    "repo_url": f"https://github.com/user/repo{i}.git",
                    "branch": "main",
                    "init_prompt": f"Test project {i}",
                },
            )

        # 列出專案
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "projects" in data
        assert data["total"] >= 3
        assert len(data["projects"]) >= 3


@pytest.mark.asyncio
async def test_delete_project():
    """測試刪除專案"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先建立專案
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/user/repo.git",
                "branch": "main",
                "init_prompt": "Test project",
            },
        )
        project_id = create_response.json()["id"]

        # 刪除專案
        response = await client.delete(f"/api/v1/projects/{project_id}")
        assert response.status_code == 204

        # 確認已刪除
        get_response = await client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404

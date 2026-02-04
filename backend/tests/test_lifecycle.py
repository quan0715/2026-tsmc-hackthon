"""容器生命週期 API 測試"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_stop_project():
    """測試停止專案"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先建立專案
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
                "spec": "測試停止",
            },
        )
        project_id = create_response.json()["id"]

        # Provision 專案
        await client.post(f"/api/v1/projects/{project_id}/provision")

        # 停止專案
        response = await client.post(f"/api/v1/projects/{project_id}/stop")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "STOPPED"

        # 清理
        await client.delete(f"/api/v1/projects/{project_id}")


@pytest.mark.asyncio
async def test_stop_project_without_provision():
    """測試停止未 provision 的專案"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 建立專案但不 provision
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
                "spec": "測試",
            },
        )
        project_id = create_response.json()["id"]

        # 嘗試停止專案
        response = await client.post(f"/api/v1/projects/{project_id}/stop")

        assert response.status_code == 400
        assert "尚未 provision" in response.json()["detail"]

        # 清理
        await client.delete(f"/api/v1/projects/{project_id}")


@pytest.mark.asyncio
async def test_delete_project():
    """測試刪除專案"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先建立專案
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
                "spec": "測試刪除",
            },
        )
        project_id = create_response.json()["id"]

        # Provision 專案
        await client.post(f"/api/v1/projects/{project_id}/provision")

        # 刪除專案
        response = await client.delete(f"/api/v1/projects/{project_id}")

        assert response.status_code == 204

        # 確認專案已刪除
        get_response = await client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_project_without_provision():
    """測試刪除未 provision 的專案"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 建立專案但不 provision
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
                "spec": "測試",
            },
        )
        project_id = create_response.json()["id"]

        # 刪除專案
        response = await client.delete(f"/api/v1/projects/{project_id}")

        assert response.status_code == 204

        # 確認專案已刪除
        get_response = await client.get(f"/api/v1/projects/{project_id}")
        assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_project():
    """測試刪除不存在的專案"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.delete(
            "/api/v1/projects/000000000000000000000000"
        )

        assert response.status_code == 404

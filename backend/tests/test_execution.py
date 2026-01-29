"""執行指令 API 測試"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_exec_command():
    """測試執行指令"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先建立專案
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
                "init_prompt": "測試執行",
            },
        )
        project_id = create_response.json()["id"]

        # Provision 專案
        await client.post(f"/api/v1/projects/{project_id}/provision")

        # 執行指令
        response = await client.post(
            f"/api/v1/projects/{project_id}/exec",
            json={"command": "ls -la", "workdir": "/workspace/repo"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exit_code"] == 0
        assert "README" in data["stdout"]
        assert data["stderr"] == ""


@pytest.mark.asyncio
async def test_exec_command_with_error():
    """測試執行錯誤指令"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先建立並 provision 專案
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
                "init_prompt": "測試錯誤",
            },
        )
        project_id = create_response.json()["id"]
        await client.post(f"/api/v1/projects/{project_id}/provision")

        # 執行不存在的指令
        response = await client.post(
            f"/api/v1/projects/{project_id}/exec",
            json={"command": "nonexistent-command"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exit_code"] != 0
        assert "not found" in data["stderr"]


@pytest.mark.asyncio
async def test_exec_without_provision():
    """測試未 provision 的專案執行指令"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 建立專案但不 provision
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
                "init_prompt": "測試",
            },
        )
        project_id = create_response.json()["id"]

        # 嘗試執行指令
        response = await client.post(
            f"/api/v1/projects/{project_id}/exec", json={"command": "ls"}
        )

        assert response.status_code == 400
        assert "尚未 provision" in response.json()["detail"]


@pytest.mark.asyncio
async def test_exec_nonexistent_project():
    """測試不存在的專案執行指令"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/projects/000000000000000000000000/exec",
            json={"command": "ls"},
        )

        assert response.status_code == 404

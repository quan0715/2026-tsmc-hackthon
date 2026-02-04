"""錯誤處理與狀態一致性測試"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_provision_with_invalid_repo():
    """測試 provision 失敗場景 - 無效的 repo URL"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 建立專案（使用無效的 repo URL）
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/invalid/nonexistent-repo-12345.git",
                "branch": "main",
                "spec": "測試失敗",
            },
        )
        project_id = create_response.json()["id"]

        # 嘗試 provision
        provision_response = await client.post(
            f"/api/v1/projects/{project_id}/provision"
        )

        # 應該失敗
        assert provision_response.status_code == 500

        # 查詢專案狀態
        get_response = await client.get(f"/api/v1/projects/{project_id}")
        data = get_response.json()

        # 狀態應該是 FAILED
        assert data["status"] == "FAILED"
        # 應該有錯誤訊息
        assert data["last_error"] is not None
        assert "Clone repository 失敗" in data["last_error"]
        # 容器應該已被清理
        assert data["docker_status"] is None or data["docker_status"]["status"] == "not_found"

        # 清理
        await client.delete(f"/api/v1/projects/{project_id}")


@pytest.mark.asyncio
async def test_provision_with_invalid_branch():
    """測試 provision 失敗場景 - 無效的分支"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 建立專案（使用不存在的分支）
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "nonexistent-branch-12345",
                "spec": "測試失敗",
            },
        )
        project_id = create_response.json()["id"]

        # 嘗試 provision
        provision_response = await client.post(
            f"/api/v1/projects/{project_id}/provision"
        )

        # 應該失敗
        assert provision_response.status_code == 500

        # 查詢專案狀態
        get_response = await client.get(f"/api/v1/projects/{project_id}")
        data = get_response.json()

        # 狀態應該是 FAILED
        assert data["status"] == "FAILED"
        # 應該有錯誤訊息
        assert data["last_error"] is not None
        # 容器應該已被清理
        assert data["docker_status"] is None or data["docker_status"]["status"] == "not_found"

        # 清理
        await client.delete(f"/api/v1/projects/{project_id}")


@pytest.mark.asyncio
async def test_docker_status_consistency():
    """測試 Docker 狀態一致性檢查"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 建立並 provision 專案
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
                "spec": "測試狀態一致性",
            },
        )
        project_id = create_response.json()["id"]

        await client.post(f"/api/v1/projects/{project_id}/provision")

        # 查詢專案（包含 Docker 狀態）
        get_response = await client.get(
            f"/api/v1/projects/{project_id}?include_docker_status=true"
        )
        data = get_response.json()

        # 應該包含 docker_status
        assert "docker_status" in data
        assert data["docker_status"] is not None
        # Docker 狀態應該是 running
        assert data["docker_status"]["status"] == "running"
        # 不應該有不一致標記
        assert data["docker_status"].get("inconsistent") is not True

        # 清理
        await client.delete(f"/api/v1/projects/{project_id}")


@pytest.mark.asyncio
async def test_get_project_without_docker_status():
    """測試查詢專案不包含 Docker 狀態"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 建立專案
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
                "spec": "測試",
            },
        )
        project_id = create_response.json()["id"]

        # 查詢專案（不包含 Docker 狀態）
        get_response = await client.get(
            f"/api/v1/projects/{project_id}?include_docker_status=false"
        )
        data = get_response.json()

        # docker_status 應該是 None
        assert data.get("docker_status") is None

        # 清理
        await client.delete(f"/api/v1/projects/{project_id}")

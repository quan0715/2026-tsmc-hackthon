"""端到端整合測試 - 完整專案生命週期"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_complete_project_lifecycle():
    """測試完整的專案生命週期"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. 建立專案
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
                "spec": "E2E 測試",
            },
        )
        assert create_response.status_code == 201
        project_id = create_response.json()["id"]
        assert create_response.json()["status"] == "CREATED"

        # 2. Provision 專案
        provision_response = await client.post(
            f"/api/v1/projects/{project_id}/provision"
        )
        assert provision_response.status_code == 200
        provision_data = provision_response.json()
        assert provision_data["status"] == "READY"
        assert provision_data["container_id"] is not None

        # 3. 查詢專案狀態（包含 Docker 狀態）
        get_response = await client.get(
            f"/api/v1/projects/{project_id}?include_docker_status=true"
        )
        assert get_response.status_code == 200
        project_data = get_response.json()
        assert project_data["status"] == "READY"
        assert project_data["docker_status"] is not None
        assert project_data["docker_status"]["status"] == "running"

        # 4. 執行指令
        exec_response = await client.post(
            f"/api/v1/projects/{project_id}/exec",
            json={"command": "ls -la", "workdir": "/workspace/repo"},
        )
        assert exec_response.status_code == 200
        exec_data = exec_response.json()
        assert exec_data["exit_code"] == 0
        assert "README" in exec_data["stdout"]

        # 5. 停止專案
        stop_response = await client.post(f"/api/v1/projects/{project_id}/stop")
        assert stop_response.status_code == 200
        assert stop_response.json()["status"] == "STOPPED"

        # 6. 刪除專案
        delete_response = await client.delete(f"/api/v1/projects/{project_id}")
        assert delete_response.status_code == 204

        # 7. 確認專案已刪除
        get_after_delete = await client.get(f"/api/v1/projects/{project_id}")
        assert get_after_delete.status_code == 404


@pytest.mark.asyncio
async def test_error_handling_workflow():
    """測試錯誤處理流程"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 1. 建立專案（無效分支）
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "invalid-branch",
                "spec": "錯誤測試",
            },
        )
        project_id = create_response.json()["id"]

        # 2. Provision 應該失敗
        provision_response = await client.post(
            f"/api/v1/projects/{project_id}/provision"
        )
        assert provision_response.status_code == 500

        # 3. 查詢狀態，應該是 FAILED
        get_response = await client.get(f"/api/v1/projects/{project_id}")
        project_data = get_response.json()
        assert project_data["status"] == "FAILED"
        assert project_data["last_error"] is not None
        assert "Clone repository 失敗" in project_data["last_error"]

        # 4. 容器應該已被清理
        assert (
            project_data["docker_status"] is None
            or project_data["docker_status"]["status"] == "not_found"
        )

        # 5. 清理
        await client.delete(f"/api/v1/projects/{project_id}")


@pytest.mark.asyncio
async def test_multiple_projects():
    """測試多個專案並行"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 建立多個專案
        project_ids = []
        for i in range(3):
            response = await client.post(
                "/api/v1/projects",
                json={
                    "repo_url": "https://github.com/octocat/Hello-World.git",
                    "branch": "master",
                    "spec": f"並行測試 {i}",
                },
            )
            assert response.status_code == 201
            project_ids.append(response.json()["id"])

        # Provision 所有專案
        for project_id in project_ids:
            response = await client.post(f"/api/v1/projects/{project_id}/provision")
            assert response.status_code == 200

        # 列出專案
        list_response = await client.get("/api/v1/projects")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert list_data["total"] >= 3

        # 清理所有專案
        for project_id in project_ids:
            await client.delete(f"/api/v1/projects/{project_id}")


@pytest.mark.asyncio
async def test_logs_streaming():
    """測試日誌串流"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 建立並 provision 專案
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
                "spec": "日誌測試",
            },
        )
        project_id = create_response.json()["id"]
        await client.post(f"/api/v1/projects/{project_id}/provision")

        # 串流日誌
        async with client.stream(
            "GET",
            f"/api/v1/projects/{project_id}/logs/stream?follow=false&tail=5",
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # 讀取部分內容
            content = await response.aread()
            content_str = content.decode("utf-8")

            # 應該包含 SSE 格式
            assert "data:" in content_str or "event:" in content_str

        # 清理
        await client.delete(f"/api/v1/projects/{project_id}")

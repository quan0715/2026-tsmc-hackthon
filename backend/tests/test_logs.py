"""日誌串流 API 測試"""
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_stream_logs():
    """測試日誌串流"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        # 先建立專案
        create_response = await client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/octocat/Hello-World.git",
                "branch": "master",
                "init_prompt": "測試日誌",
            },
        )
        project_id = create_response.json()["id"]

        # Provision 專案
        await client.post(f"/api/v1/projects/{project_id}/provision")

        # 串流日誌 (不 follow,只取最後幾行)
        async with client.stream(
            "GET",
            f"/api/v1/projects/{project_id}/logs/stream?follow=false&tail=10",
        ) as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

            # 讀取 SSE 事件
            content = await response.aread()
            content_str = content.decode("utf-8")

            # 應該包含 SSE 格式的資料
            assert "data:" in content_str or "event:" in content_str


@pytest.mark.asyncio
async def test_stream_logs_without_provision():
    """測試未 provision 的專案串流日誌"""
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

        # 嘗試串流日誌
        response = await client.get(
            f"/api/v1/projects/{project_id}/logs/stream?follow=false"
        )

        assert response.status_code == 400
        assert "尚未 provision" in response.json()["detail"]


@pytest.mark.asyncio
async def test_stream_logs_nonexistent_project():
    """測試不存在的專案串流日誌"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/projects/000000000000000000000000/logs/stream"
        )

        assert response.status_code == 404

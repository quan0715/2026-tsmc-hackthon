"""AgentRun 服務測試

只測試在生產環境中實際使用的方法。
"""
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
from app.services.agent_run_service import AgentRunService
from app.models.agent_run import AgentPhase, AgentRunStatus


@pytest.fixture
async def db():
    """取得測試資料庫連接"""
    client = AsyncIOMotorClient(settings.mongodb_url)
    db = client[settings.mongodb_database]
    yield db
    # 清理測試資料
    await db.agent_runs.delete_many({})
    client.close()


@pytest.fixture
async def agent_run_service(db):
    """建立 AgentRunService 實例"""
    return AgentRunService(db)


@pytest.mark.asyncio
async def test_create_agent_run(agent_run_service):
    """測試建立 AgentRun"""
    project_id = "test_project_123"

    agent_run = await agent_run_service.create_agent_run(
        project_id=project_id,
        artifacts_path="/workspace/artifacts"
    )

    assert agent_run is not None
    assert agent_run.id is not None
    assert agent_run.project_id == project_id
    assert agent_run.iteration_index == 1
    assert agent_run.phase == AgentPhase.PLAN
    assert agent_run.status == AgentRunStatus.RUNNING
    assert agent_run.artifacts_path == "/workspace/artifacts"


@pytest.mark.asyncio
async def test_get_agent_run_by_id(agent_run_service):
    """測試根據 ID 查詢 AgentRun"""
    project_id = "test_project_456"

    # 建立 AgentRun
    created = await agent_run_service.create_agent_run(project_id=project_id)

    # 查詢
    fetched = await agent_run_service.get_agent_run_by_id(created.id)

    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.project_id == project_id


@pytest.mark.asyncio
async def test_get_agent_run_by_invalid_id(agent_run_service):
    """測試使用無效 ID 查詢 AgentRun"""
    # 無效的 ObjectId 格式
    result = await agent_run_service.get_agent_run_by_id("invalid_id")
    assert result is None

    # 不存在的 ObjectId
    result = await agent_run_service.get_agent_run_by_id("507f1f77bcf86cd799439011")
    assert result is None


@pytest.mark.asyncio
async def test_get_agent_runs_by_project(agent_run_service):
    """測試根據 project_id 查詢所有 AgentRuns"""
    project_id = "test_project_mno"

    # 建立多個 AgentRuns
    run1 = await agent_run_service.create_agent_run(project_id=project_id)
    run2 = await agent_run_service.create_agent_run(project_id=project_id)
    run3 = await agent_run_service.create_agent_run(project_id=project_id)

    # 查詢
    runs, total = await agent_run_service.get_agent_runs_by_project(project_id)

    assert total == 3
    assert len(runs) == 3
    # 應該依建立時間倒序（最新的在前）
    assert runs[0].id == run3.id
    assert runs[1].id == run2.id
    assert runs[2].id == run1.id


@pytest.mark.asyncio
async def test_get_agent_runs_by_project_with_pagination(agent_run_service):
    """測試分頁查詢"""
    project_id = "test_project_pagination"

    # 建立 5 個 AgentRuns
    for _ in range(5):
        await agent_run_service.create_agent_run(project_id=project_id)

    # 查詢第一頁（2 筆）
    runs, total = await agent_run_service.get_agent_runs_by_project(
        project_id, skip=0, limit=2
    )
    assert total == 5
    assert len(runs) == 2

    # 查詢第二頁（2 筆）
    runs, total = await agent_run_service.get_agent_runs_by_project(
        project_id, skip=2, limit=2
    )
    assert total == 5
    assert len(runs) == 2


@pytest.mark.asyncio
async def test_mark_failed(agent_run_service):
    """測試標記為失敗"""
    project_id = "test_project_jkl"

    # 建立 AgentRun
    agent_run = await agent_run_service.create_agent_run(project_id=project_id)
    assert agent_run.status == AgentRunStatus.RUNNING

    # 標記為失敗
    error_msg = "LLM API 超時"
    updated = await agent_run_service.mark_failed(agent_run.id, error_msg)
    assert updated is not None
    assert updated.status == AgentRunStatus.FAILED
    assert updated.error_message == error_msg
    assert updated.finished_at is not None


@pytest.mark.asyncio
async def test_mark_failed_with_invalid_id(agent_run_service):
    """測試使用無效 ID 標記失敗"""
    result = await agent_run_service.mark_failed("invalid_id", "error")
    assert result is None


@pytest.mark.asyncio
async def test_delete_agent_runs_by_project(agent_run_service):
    """測試刪除專案的所有 AgentRuns"""
    project_id = "test_project_delete"

    # 建立多個 AgentRuns
    await agent_run_service.create_agent_run(project_id=project_id)
    await agent_run_service.create_agent_run(project_id=project_id)
    await agent_run_service.create_agent_run(project_id=project_id)

    # 確認已建立
    runs, total = await agent_run_service.get_agent_runs_by_project(project_id)
    assert total == 3

    # 批量刪除
    deleted_count = await agent_run_service.delete_agent_runs_by_project(project_id)
    assert deleted_count == 3

    # 確認已刪除
    runs, total = await agent_run_service.get_agent_runs_by_project(project_id)
    assert total == 0


@pytest.mark.asyncio
async def test_delete_agent_runs_by_nonexistent_project(agent_run_service):
    """測試刪除不存在專案的 AgentRuns"""
    deleted_count = await agent_run_service.delete_agent_runs_by_project("nonexistent")
    assert deleted_count == 0

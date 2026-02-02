"""Simplified Agent API - Container AI Server 代理"""
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase
from sse_starlette.sse import EventSourceResponse
import httpx
import logging

from ..database.mongodb import get_database
from ..services.project_service import ProjectService
from ..models.user import User
from ..models.project import ProjectStatus
from ..dependencies.auth import get_current_user

router = APIRouter(prefix="/api/v1/projects", tags=["agent"])
logger = logging.getLogger(__name__)


async def get_project_service(
    db: AsyncDatabase = Depends(get_database),
) -> ProjectService:
    """依賴注入：獲取 ProjectService"""
    return ProjectService(db)


@router.post("/{project_id}/cloud-run")
async def run_cloud_agent(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user),
):
    """啟動 AI Agent 執行（異步模式）

    流程：
    1. 驗證專案權限和狀態（必須是 READY）
    2. 呼叫容器 /run endpoint（啟動 Agent）
    3. 立即返回 task_id

    註：repo 已在 provision 時 clone，無需再次 clone
    """
    # 1. 驗證專案存在和權限
    project = await project_service.get_project_by_id(project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="專案不存在或無權限")

    if project.status != ProjectStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"專案狀態必須為 READY，目前為 {project.status}"
        )

    container_name = f"refactor-project-{project_id}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 2. 啟動 Agent（repo 已在 provision 時 clone）
            logger.info(f"呼叫容器 run: {container_name}")
            run_response = await client.post(
                f"http://{container_name}:8000/run",
                json={
                    "init_prompt": project.init_prompt,
                    "verbose": True
                }
            )
            run_response.raise_for_status()
            result = run_response.json()

        logger.info(f"Agent 任務已啟動: project={project_id}, task_id={result['task_id']}")
        return {
            "status": "success",
            "task_id": result["task_id"],
            "message": "Agent 任務已啟動，正在背景執行"
        }

    except httpx.HTTPError as e:
        logger.error(f"AI Server 呼叫失敗: {e}")
        raise HTTPException(status_code=503, detail=f"AI Server 錯誤: {str(e)}")


@router.get("/{project_id}/cloud-run/{task_id}")
async def get_task_status(
    project_id: str,
    task_id: str,
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user),
):
    """查詢 Agent 任務執行狀態"""
    # 驗證專案權限
    project = await project_service.get_project_by_id(project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="專案不存在或無權限")

    container_name = f"refactor-project-{project_id}"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"http://{container_name}:8000/tasks/{task_id}"
            )
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"查詢任務狀態失敗: {e}")
        raise HTTPException(status_code=503, detail="無法查詢任務狀態")


@router.get("/{project_id}/cloud-run/{task_id}/stream")
async def stream_task_logs(
    project_id: str,
    task_id: str,
    project_service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user),
):
    """SSE 串流 Agent 執行日誌（轉發容器的 stream）"""
    # 驗證專案權限
    project = await project_service.get_project_by_id(project_id)
    if not project or project.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="專案不存在或無權限")

    container_name = f"refactor-project-{project_id}"

    async def event_generator():
        """轉發容器的 SSE stream"""
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream(
                    "GET",
                    f"http://{container_name}:8000/tasks/{task_id}/stream"
                ) as response:
                    async for line in response.aiter_lines():
                        if line:
                            yield line + "\n"
        except Exception as e:
            logger.error(f"Stream 轉發失敗: {e}")
            yield f"event: error\ndata: {str(e)}\n\n"

    return EventSourceResponse(event_generator())

"""Agent API - 代理 Container AI Server 的通訊"""
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase
from sse_starlette.sse import EventSourceResponse
from starlette.responses import StreamingResponse
import httpx
import logging
import uuid

from ..database.mongodb import get_database
from ..services.project_service import ProjectService
from ..models.project import ProjectStatus
from ..dependencies.auth import get_current_user, verify_project_access

router = APIRouter(prefix="/api/v1/projects", tags=["agent"])
logger = logging.getLogger(__name__)

# Agent 狀態映射：從 AI Server 狀態轉換為前端期望格式
AGENT_STATUS_MAPPING = {
    "pending": "RUNNING",
    "running": "RUNNING",
    "success": "DONE",
    "failed": "FAILED",
    "stopped": "STOPPED"
}


def get_container_name(project_id: str) -> str:
    """獲取容器名稱"""
    return f"refactor-project-{project_id}"


async def get_project_service(
    db: AsyncDatabase = Depends(get_database),
) -> ProjectService:
    """依賴注入：獲取 ProjectService"""
    return ProjectService(db)


@router.post("/{project_id}/agent/run")
async def run_agent(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """啟動 AI Agent 執行（異步模式）

    流程：
    1. 驗證專案權限和狀態（必須是 READY）
    2. 檢查或生成 refactor_thread_id（用於會話持久化）
    3. 呼叫容器內的 AI Server /run endpoint
    4. 立即返回 run_id，Agent 在背景執行
    """
    if project.status != ProjectStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"專案狀態必須為 READY，目前為 {project.status}"
        )

    container_name = get_container_name(project_id)

    # 檢查或生成 refactor_thread_id
    thread_id = project.refactor_thread_id
    if not thread_id:
        thread_id = f"refactor-{project_id}-{uuid.uuid4()}"
        # 儲存 thread_id 到專案
        await project_service.update_project(project_id, {"refactor_thread_id": thread_id})
        logger.info(f"生成新的 refactor_thread_id: {thread_id}")
    else:
        logger.info(f"使用現有的 refactor_thread_id: {thread_id}")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"呼叫容器 AI Server: {container_name}")
            run_response = await client.post(
                f"http://{container_name}:8000/run",
                json={
                    "spec": project.spec,
                    "thread_id": thread_id,
                    "verbose": True
                }
            )
            run_response.raise_for_status()
            result = run_response.json()

        logger.info(f"Agent 任務已啟動: project={project_id}, task_id={result['task_id']}, thread_id={thread_id}")

        # 轉換為前端期望格式
        return {
            "run_id": result["task_id"],
            "project_id": project_id,
            "thread_id": thread_id,
            "status": "RUNNING",
            "iteration_index": 0,
            "phase": "plan",
            "created_at": result.get("created_at", ""),
            "message": "Agent 任務已啟動，正在背景執行"
        }

    except httpx.HTTPError as e:
        logger.error(f"AI Server 呼叫失敗: {e}")
        raise HTTPException(status_code=503, detail=f"AI Server 錯誤: {str(e)}")


@router.get("/{project_id}/agent/runs")
async def list_agent_runs(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """列出專案的所有 Agent Runs"""
    container_name = get_container_name(project_id)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"http://{container_name}:8000/tasks"
            )
            response.raise_for_status()
            tasks_data = response.json()

        runs = []
        for task in tasks_data.get("tasks", []):
            runs.append({
                "id": task["task_id"],
                "project_id": project_id,
                "iteration_index": 0,
                "phase": "plan",
                "status": AGENT_STATUS_MAPPING.get(task["status"], "RUNNING"),
                "created_at": task.get("created_at", ""),
                "updated_at": task.get("started_at", task.get("created_at", "")),
                "finished_at": task.get("finished_at"),
                "error_message": task.get("error_message"),
            })

        return {
            "total": len(runs),
            "runs": runs
        }

    except httpx.HTTPError as e:
        logger.error(f"查詢 Agent Runs 失敗: {e}")
        # 如果容器未啟動，返回空列表
        return {"total": 0, "runs": []}


@router.get("/{project_id}/agent/runs/{run_id}")
async def get_agent_run_detail(
    project_id: str,
    run_id: str,
    project_service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """查詢 Agent Run 詳細狀態"""
    container_name = get_container_name(project_id)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"http://{container_name}:8000/tasks/{run_id}"
            )
            response.raise_for_status()
            task_data = response.json()

        return {
            "id": run_id,
            "project_id": project_id,
            "iteration_index": 0,
            "phase": "plan",
            "status": AGENT_STATUS_MAPPING.get(task_data["status"], "RUNNING"),
            "created_at": task_data.get("created_at", ""),
            "updated_at": task_data.get("started_at", task_data.get("created_at", "")),
            "finished_at": task_data.get("finished_at"),
            "error_message": task_data.get("error_message"),
        }

    except httpx.HTTPError as e:
        logger.error(f"查詢任務狀態失敗: {e}")
        raise HTTPException(status_code=503, detail="無法查詢任務狀態")


@router.get("/{project_id}/agent/runs/{run_id}/stream")
async def stream_agent_logs(
    project_id: str,
    run_id: str,
    project_service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """SSE 串流 Agent 執行日誌（轉發容器的 stream）"""
    container_name = get_container_name(project_id)

    async def event_generator():
        """直接轉發容器的 SSE stream（原始轉發，不做任何處理）"""
        try:
            url = f"http://{container_name}:8000/tasks/{run_id}/stream"
            logger.info(f"🔗 開始串流 AI Server 日誌: {url}")

            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", url) as response:
                    logger.info(f"✅ SSE 連線已建立，狀態碼: {response.status_code}")

                    line_count = 0
                    async for line in response.aiter_lines():
                        line_count += 1
                        # 直接轉發原始行（不做任何包裝）
                        yield (line + "\n").encode('utf-8')

            logger.info(f"✅ SSE 串流正常結束: run_id={run_id}, 共 {line_count} 行")

        except httpx.HTTPError as e:
            error_msg = f"HTTP 錯誤: {str(e)}"
            logger.error(f"❌ {error_msg}")
            yield f"event: error\ndata: {error_msg}\n\n".encode('utf-8')
        except Exception as e:
            error_msg = f"Stream 轉發失敗: {str(e)}"
            logger.error(f"❌ {error_msg}")
            yield f"event: error\ndata: {error_msg}\n\n".encode('utf-8')

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.post("/{project_id}/agent/runs/{run_id}/stop")
async def stop_agent_run(
    project_id: str,
    run_id: str,
    project_service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """停止執行中的 Agent Run"""
    container_name = get_container_name(project_id)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"http://{container_name}:8000/tasks/{run_id}/stop"
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"Agent Run 已停止: project={project_id}, run_id={run_id}")
        return result

    except httpx.HTTPError as e:
        logger.error(f"停止 Agent Run 失敗: {e}")
        raise HTTPException(status_code=503, detail=f"AI Server 錯誤: {str(e)}")


@router.post("/{project_id}/agent/runs/{run_id}/resume")
async def resume_agent_run(
    project_id: str,
    run_id: str,
    project_service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """繼續執行已停止的 Agent Run

    使用現有的 thread_id 繼續對話，並傳送最新的 spec 作為新訊息。
    這樣 Agent 可以在原有上下文中繼續工作。
    """
    container_name = get_container_name(project_id)

    # 確保有 thread_id
    thread_id = project.refactor_thread_id
    if not thread_id:
        raise HTTPException(
            status_code=400,
            detail="專案沒有進行中的重構會話，請使用「開始重構」"
        )

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 使用 /run endpoint 而非 /resume，因為我們要傳送新的 spec
            # 但保持同一個 thread_id 來延續對話
            response = await client.post(
                f"http://{container_name}:8000/run",
                json={
                    "spec": project.spec,
                    "thread_id": thread_id,
                    "verbose": True
                }
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"Agent Run 已恢復: project={project_id}, thread_id={thread_id}, new_task_id={result['task_id']}")

        # 轉換為前端期望格式
        return {
            "run_id": result["task_id"],
            "old_run_id": run_id,
            "project_id": project_id,
            "thread_id": thread_id,
            "status": "RUNNING",
            "iteration_index": 0,
            "phase": "plan",
            "created_at": result.get("created_at", ""),
            "message": "Agent 任務已恢復，正在背景執行"
        }

    except httpx.HTTPError as e:
        logger.error(f"恢復 Agent Run 失敗: {e}")
        raise HTTPException(status_code=503, detail=f"AI Server 錯誤: {str(e)}")


@router.post("/{project_id}/agent/reset-session")
async def reset_refactor_session(
    project_id: str,
    project_service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """重設重構會話

    清空 refactor_thread_id，下次開始重構時會建立新的會話。
    這會讓 Agent 忘記之前的對話歷史，從頭開始。
    """
    if not project.refactor_thread_id:
        return {
            "project_id": project_id,
            "message": "專案沒有進行中的重構會話"
        }

    old_thread_id = project.refactor_thread_id

    # 清空 thread_id
    await project_service.update_project(project_id, {"refactor_thread_id": None})

    logger.info(f"重設重構會話: project={project_id}, old_thread_id={old_thread_id}")

    return {
        "project_id": project_id,
        "old_thread_id": old_thread_id,
        "message": "重構會話已重設，下次開始重構時會建立新的會話"
    }

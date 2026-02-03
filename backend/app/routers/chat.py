"""Chat API - 聊天模式（支援多輪對話）"""
from fastapi import APIRouter, Depends, HTTPException
from pymongo.asynchronous.database import AsyncDatabase
from starlette.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
import httpx
import logging
import uuid

from ..database.mongodb import get_database
from ..services.project_service import ProjectService
from ..models.project import ProjectStatus
from ..dependencies.auth import verify_project_access

router = APIRouter(prefix="/api/v1/projects", tags=["chat"])
logger = logging.getLogger(__name__)


class ChatMessageRequest(BaseModel):
    """聊天訊息請求"""
    message: str
    thread_id: Optional[str] = None  # 不提供則自動生成
    verbose: bool = True


class ChatMessageResponse(BaseModel):
    """聊天訊息回應"""
    task_id: str
    thread_id: str
    project_id: str
    status: str
    message: str


def get_container_name(project_id: str) -> str:
    """獲取容器名稱"""
    return f"refactor-project-{project_id}"


async def get_project_service(
    db: AsyncDatabase = Depends(get_database),
) -> ProjectService:
    """依賴注入：獲取 ProjectService"""
    return ProjectService(db)


@router.post("/{project_id}/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    project_id: str,
    request: ChatMessageRequest,
    project=Depends(verify_project_access),
):
    """發送聊天訊息

    支援多輪對話：
    - 使用相同的 thread_id 可以維持對話上下文
    - 不提供 thread_id 則自動生成新的對話 ID
    - 對話狀態會透過 PostgreSQL 持久化（如果配置了）
    """
    # 檢查專案狀態
    if project.status != ProjectStatus.READY:
        raise HTTPException(
            status_code=400,
            detail=f"專案狀態必須為 READY，目前為 {project.status}"
        )

    # 生成或使用提供的 thread_id
    thread_id = request.thread_id or f"chat-{project_id}-{uuid.uuid4()}"

    container_name = get_container_name(project_id)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"發送聊天訊息到容器: {container_name}, thread: {thread_id}")
            response = await client.post(
                f"http://{container_name}:8000/chat",
                json={
                    "message": request.message,
                    "thread_id": thread_id,
                    "verbose": request.verbose
                }
            )
            response.raise_for_status()
            result = response.json()

        logger.info(
            f"聊天任務已啟動: project={project_id}, task_id={result['task_id']}"
        )

        return ChatMessageResponse(
            task_id=result["task_id"],
            thread_id=result["thread_id"],
            project_id=project_id,
            status="RUNNING",
            message="聊天任務已啟動，正在背景執行"
        )

    except httpx.HTTPError as e:
        logger.error(f"聊天請求失敗: {e}")
        raise HTTPException(status_code=503, detail=f"AI Server 錯誤: {str(e)}")


@router.get("/{project_id}/chat/{task_id}/stream")
async def stream_chat_response(
    project_id: str,
    task_id: str,
    project=Depends(verify_project_access),
):
    """SSE 串流聊天回應

    串流返回 AI 的回應，支援以下事件類型：
    - log: 一般日誌訊息
    - text_delta: 文字增量
    - tool_call_start: 工具呼叫開始
    - tool_call_result: 工具呼叫結果
    - token_usage: Token 使用統計
    - status: 任務狀態更新
    """
    container_name = get_container_name(project_id)

    async def event_generator():
        """直接轉發容器的 SSE stream"""
        try:
            url = f"http://{container_name}:8000/tasks/{task_id}/stream"
            logger.info(f"開始串流聊天回應: {url}")

            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("GET", url) as response:
                    logger.info(f"SSE 連線已建立，狀態碼: {response.status_code}")

                    async for line in response.aiter_lines():
                        yield (line + "\n").encode('utf-8')

            logger.info(f"SSE 串流正常結束: task_id={task_id}")

        except httpx.HTTPError as e:
            error_msg = f"HTTP 錯誤: {str(e)}"
            logger.error(f"{error_msg}")
            yield f"event: error\ndata: {error_msg}\n\n".encode('utf-8')
        except Exception as e:
            error_msg = f"Stream 轉發失敗: {str(e)}"
            logger.error(f"{error_msg}")
            yield f"event: error\ndata: {error_msg}\n\n".encode('utf-8')

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/{project_id}/chat/{task_id}/status")
async def get_chat_status(
    project_id: str,
    task_id: str,
    project=Depends(verify_project_access),
):
    """查詢聊天任務狀態"""
    container_name = get_container_name(project_id)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(
                f"http://{container_name}:8000/tasks/{task_id}"
            )
            response.raise_for_status()
            task_data = response.json()

        # 轉換狀態格式
        status_mapping = {
            "pending": "RUNNING",
            "running": "RUNNING",
            "success": "DONE",
            "failed": "FAILED",
            "stopped": "STOPPED"
        }

        return {
            "task_id": task_id,
            "thread_id": task_data.get("thread_id"),
            "project_id": project_id,
            "status": status_mapping.get(task_data["status"], "RUNNING"),
            "created_at": task_data.get("created_at"),
            "started_at": task_data.get("started_at"),
            "finished_at": task_data.get("finished_at"),
            "error_message": task_data.get("error_message"),
        }

    except httpx.HTTPError as e:
        logger.error(f"查詢聊天狀態失敗: {e}")
        raise HTTPException(status_code=503, detail="無法查詢任務狀態")


@router.post("/{project_id}/chat/{task_id}/stop")
async def stop_chat(
    project_id: str,
    task_id: str,
    project=Depends(verify_project_access),
):
    """停止執行中的聊天任務"""
    container_name = get_container_name(project_id)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"http://{container_name}:8000/tasks/{task_id}/stop"
            )
            response.raise_for_status()
            result = response.json()

        logger.info(f"聊天任務已停止: project={project_id}, task_id={task_id}")
        return result

    except httpx.HTTPError as e:
        logger.error(f"停止聊天任務失敗: {e}")
        raise HTTPException(status_code=503, detail=f"AI Server 錯誤: {str(e)}")

"""Chat API - 聊天模式（支援多輪對話）"""
from fastapi import APIRouter, Depends, HTTPException
from pymongo.asynchronous.database import AsyncDatabase
from starlette.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List
import httpx
import logging
import uuid

from ..database.mongodb import get_database
from ..services.project_service import ProjectService
from ..services.chat_session_service import ChatSessionService
from ..models.project import ProjectStatus
from ..dependencies.auth import verify_project_access

router = APIRouter(prefix="/api/v1/projects", tags=["chat"])
logger = logging.getLogger(__name__)


class ChatMessageRequest(BaseModel):
    """聊天訊息請求"""
    message: str
    thread_id: Optional[str] = None  # 不提供則自動生成
    verbose: bool = True
    model: Optional[str] = None  # 模型 ID


class ChatMessageResponse(BaseModel):
    """聊天訊息回應"""
    task_id: str
    thread_id: str
    project_id: str
    status: str
    message: str


class ChatSessionResponse(BaseModel):
    """聊天會話回應"""
    thread_id: str
    project_id: str
    title: Optional[str] = None
    created_at: str
    last_message_at: str


class ChatSessionListResponse(BaseModel):
    """聊天會話列表回應"""
    total: int
    sessions: List[ChatSessionResponse]


class ChatHistoryMessage(BaseModel):
    """聊天歷史訊息"""
    id: str
    role: str
    content: str
    timestamp: str
    toolName: Optional[str] = None
    toolCallId: Optional[str] = None
    toolInput: Optional[dict] = None
    toolOutput: Optional[str] = None
    tokenUsage: Optional[dict] = None


class ChatHistoryResponse(BaseModel):
    """聊天歷史回應"""
    thread_id: str
    messages: List[ChatHistoryMessage]


def get_container_name(project_id: str) -> str:
    """獲取容器名稱"""
    return f"refactor-project-{project_id}"


async def get_project_service(
    db: AsyncDatabase = Depends(get_database),
) -> ProjectService:
    """依賴注入：獲取 ProjectService"""
    return ProjectService(db)


async def get_chat_session_service(
    db: AsyncDatabase = Depends(get_database),
) -> ChatSessionService:
    """依賴注入：獲取 ChatSessionService"""
    return ChatSessionService(db)


@router.post("/{project_id}/chat", response_model=ChatMessageResponse)
async def send_chat_message(
    project_id: str,
    request: ChatMessageRequest,
    chat_session_service: ChatSessionService = Depends(get_chat_session_service),
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
    # 使用首則訊息作為 session title（僅在首次建立時生效）
    title = " ".join(request.message.strip().split())
    if len(title) > 60:
        title = title[:60].rstrip()

    container_name = get_container_name(project_id)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            logger.info(f"發送聊天訊息到容器: {container_name}, thread: {thread_id}")
            response = await client.post(
                f"http://{container_name}:8000/chat",
                json={
                    "message": request.message,
                    "thread_id": thread_id,
                    "verbose": request.verbose,
                    "model": request.model,
                }
            )
            response.raise_for_status()
            result = response.json()

        logger.info(
            f"聊天任務已啟動: project={project_id}, task_id={result['task_id']}"
        )

        # 建立或更新聊天會話
        await chat_session_service.upsert_session(project_id, thread_id, title=title)

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


@router.get("/{project_id}/chat/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    project_id: str,
    chat_session_service: ChatSessionService = Depends(get_chat_session_service),
    project=Depends(verify_project_access),
):
    """列出專案的聊天會話（依最後訊息時間排序）"""
    sessions = await chat_session_service.list_sessions(project_id)
    response_sessions = [
        ChatSessionResponse(
            thread_id=s.thread_id,
            project_id=s.project_id,
            title=s.title,
            created_at=s.created_at.isoformat(),
            last_message_at=s.last_message_at.isoformat(),
        )
        for s in sessions
    ]
    return ChatSessionListResponse(total=len(response_sessions), sessions=response_sessions)


@router.get(
    "/{project_id}/chat/sessions/{thread_id}/history",
    response_model=ChatHistoryResponse,
)
async def get_chat_history(
    project_id: str,
    thread_id: str,
    chat_session_service: ChatSessionService = Depends(get_chat_session_service),
    project=Depends(verify_project_access),
):
    """取得聊天歷史（透過容器 AI Server）"""
    # 確保 session 屬於該專案
    session = await chat_session_service.get_session(project_id, thread_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    container_name = get_container_name(project_id)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"http://{container_name}:8000/threads/{thread_id}/history"
            )
            response.raise_for_status()
            result = response.json()

        return ChatHistoryResponse(
            thread_id=result.get("thread_id", thread_id),
            messages=result.get("messages", []),
        )
    except httpx.HTTPError as e:
        logger.error(f"取得聊天歷史失敗: {e}")
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

"""Server Schemas - Pydantic models for API requests/responses"""

from pydantic import BaseModel
from typing import Optional


class TaskStatus:
    """任務狀態枚舉"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    STOPPED = "stopped"


class RunRequest(BaseModel):
    """重構執行請求"""
    spec: str  # 重構規格說明
    thread_id: Optional[str] = None  # 會話 ID（用於持久化）
    verbose: bool = True


class CloneRequest(BaseModel):
    """Clone 請求"""
    repo_url: str
    branch: str = "main"


class ChatRequest(BaseModel):
    """聊天請求（支援多輪對話）"""
    message: str
    thread_id: str
    verbose: bool = True


class ChatResponse(BaseModel):
    """聊天回應"""
    task_id: str
    thread_id: str
    status: str
    message: str


class RunResponse(BaseModel):
    """執行回應"""
    task_id: str
    status: str
    message: str


class TaskStatusResponse(BaseModel):
    """任務狀態回應"""
    task_id: str
    status: str
    created_at: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    error_message: Optional[str] = None

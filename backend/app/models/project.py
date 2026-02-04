"""專案資料模型"""
from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ProjectType(str, Enum):
    """專案類型"""

    REFACTOR = "REFACTOR"  # 重構專案（原有功能，需要 repo_url）
    SANDBOX = "SANDBOX"    # 沙盒測試（純聊天，不需要 repo_url）


class ProjectStatus(str, Enum):
    """專案狀態"""

    CREATED = "CREATED"  # 已建立
    PROVISIONING = "PROVISIONING"  # 正在建立容器
    READY = "READY"  # 容器就緒
    RUNNING = "RUNNING"  # 正在執行任務
    STOPPED = "STOPPED"  # 已停止
    FAILED = "FAILED"  # 失敗
    DELETED = "DELETED"  # 已刪除


class Project(BaseModel):
    """專案模型"""

    id: str = Field(default=None, alias="_id")  # MongoDB _id
    title: Optional[str] = None  # 專案標題（選填，未填則使用 repo 名稱）
    description: Optional[str] = None  # 專案描述（選填）
    project_type: ProjectType = ProjectType.REFACTOR  # 專案類型
    repo_url: Optional[str] = None  # Git repository URL（SANDBOX 類型可為空）
    branch: str = "main"  # Git branch
    spec: str = ""  # 重構規格說明（原 init_prompt）
    refactor_thread_id: Optional[str] = None  # 重構會話 ID
    status: ProjectStatus = ProjectStatus.CREATED  # 專案狀態
    container_id: Optional[str] = None  # Docker 容器 ID
    owner_id: str  # 擁有者用戶 ID
    owner_email: Optional[str] = None  # 擁有者 Email（冗餘欄位，提升查詢效能）
    created_at: datetime = Field(default_factory=datetime.utcnow)  # 建立時間
    updated_at: datetime = Field(default_factory=datetime.utcnow)  # 更新時間
    last_error: Optional[str] = None  # 最後錯誤訊息

    class Config:
        populate_by_name = True
        json_encoders = {datetime: lambda v: v.isoformat()}

    def model_dump(self, **kwargs):
        """序列化時轉換 _id 為 id"""
        data = super().model_dump(**kwargs)
        if "_id" in data and data["_id"]:
            data["id"] = data["_id"]
            if "by_alias" not in kwargs or not kwargs.get("by_alias"):
                del data["_id"]
        return data

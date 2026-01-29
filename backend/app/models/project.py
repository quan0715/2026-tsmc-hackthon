"""專案資料模型"""
from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


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
    repo_url: str  # Git repository URL
    branch: str = "main"  # Git branch
    init_prompt: str  # 初始提示
    status: ProjectStatus = ProjectStatus.CREATED  # 專案狀態
    container_id: Optional[str] = None  # Docker 容器 ID
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

"""專案 API Schema"""
from pydantic import BaseModel, Field, HttpUrl, model_validator
from datetime import datetime
from typing import Optional, Dict, Any, List, Literal
from ..models.project import ProjectStatus, ProjectType


class CreateProjectRequest(BaseModel):
    """建立專案請求"""

    title: Optional[str] = Field(None, description="專案標題（選填，未填則使用 repo 名稱）")
    description: Optional[str] = Field(None, description="專案描述（選填）")
    project_type: ProjectType = Field(
        default=ProjectType.REFACTOR,
        description="專案類型：REFACTOR（重構）或 SANDBOX（沙盒測試）"
    )
    repo_url: Optional[str] = Field(None, description="Git repository URL（SANDBOX 類型可不填）")
    branch: str = Field(default="main", description="Git branch")
    spec: str = Field(default="", description="重構規格說明")

    @model_validator(mode='after')
    def validate_repo_url(self):
        """驗證 REFACTOR 類型必須有 repo_url"""
        if self.project_type == ProjectType.REFACTOR and not self.repo_url:
            raise ValueError("REFACTOR 類型專案必須提供 repo_url")
        return self

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Racing Car Kata 重構專案",
                "description": "將 Racing Car Kata 的 Python 程式碼系統性轉換為 Golang",
                "project_type": "REFACTOR",
                "repo_url": "https://github.com/user/repo.git",
                "branch": "main",
                "spec": "重構專案以提升可維護性",
            }
        }


class UpdateProjectRequest(BaseModel):
    """更新專案請求"""

    title: Optional[str] = None
    description: Optional[str] = None
    repo_url: Optional[str] = None
    branch: Optional[str] = None
    spec: Optional[str] = None
    status: Optional[ProjectStatus] = None
    container_id: Optional[str] = None


class ProjectResponse(BaseModel):
    """專案回應"""

    id: str = Field(..., description="專案 ID")
    title: Optional[str] = Field(None, description="專案標題")
    description: Optional[str] = Field(None, description="專案描述")
    project_type: ProjectType = Field(..., description="專案類型")
    repo_url: Optional[str] = Field(None, description="Git repository URL")
    branch: str = Field(..., description="Git branch")
    spec: str = Field(default="", description="重構規格說明")
    refactor_thread_id: Optional[str] = Field(None, description="重構會話 ID")
    status: ProjectStatus = Field(..., description="專案狀態")
    container_id: Optional[str] = Field(None, description="Docker 容器 ID")
    created_at: datetime = Field(..., description="建立時間")
    updated_at: datetime = Field(..., description="更新時間")
    last_error: Optional[str] = Field(None, description="最後錯誤訊息")
    docker_status: Optional[Dict[str, Any]] = Field(
        None, description="Docker 容器狀態（包含實時狀態和一致性檢查）"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id": "507f1f77bcf86cd799439011",
                "title": "Racing Car Kata 重構專案",
                "description": "將 Racing Car Kata 的 Python 程式碼系統性轉換為 Golang",
                "project_type": "REFACTOR",
                "repo_url": "https://github.com/user/repo.git",
                "branch": "main",
                "spec": "重構專案以提升可維護性",
                "refactor_thread_id": None,
                "status": "CREATED",
                "container_id": None,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "last_error": None,
            }
        }


class ProjectListResponse(BaseModel):
    """專案列表回應"""

    total: int = Field(..., description="總數")
    projects: list[ProjectResponse] = Field(..., description="專案列表")


class FileTreeNode(BaseModel):
    """檔案樹節點"""

    name: str = Field(..., description="檔案或目錄名稱")
    path: str = Field(..., description="相對路徑")
    type: Literal["file", "directory"] = Field(..., description="節點類型")
    children: Optional[List["FileTreeNode"]] = Field(None, description="子節點（僅目錄有）")


class FileTreeResponse(BaseModel):
    """檔案樹回應"""

    root: str = Field(..., description="根目錄路徑")
    tree: List[FileTreeNode] = Field(..., description="檔案樹")


class FileContentResponse(BaseModel):
    """檔案內容回應"""

    path: str = Field(..., description="檔案路徑")
    content: str = Field(..., description="檔案內容")
    size: int = Field(..., description="檔案大小（bytes）")

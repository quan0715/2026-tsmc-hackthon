"""Provision API Schema"""
from pydantic import BaseModel, Field
from typing import Optional


class ProvisionResponse(BaseModel):
    """Provision 回應"""

    message: str = Field(..., description="訊息")
    project_id: str = Field(..., description="專案 ID")
    container_id: Optional[str] = Field(None, description="容器 ID")
    status: str = Field(..., description="專案狀態")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "專案 provision 成功",
                "project_id": "507f1f77bcf86cd799439011",
                "container_id": "abc123def456",
                "status": "READY",
            }
        }

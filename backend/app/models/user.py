"""用戶資料模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class User(BaseModel):
    """用戶模型"""
    id: Optional[str] = Field(default=None, alias="_id")
    email: EmailStr  # 唯一，用於登入
    username: str
    password_hash: str  # bcrypt hash
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "testuser",
                "password_hash": "$2b$12$...",
                "is_active": True,
            }
        }

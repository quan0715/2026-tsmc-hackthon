"""聊天會話資料模型"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatSession(BaseModel):
    """聊天會話模型（MongoDB）"""

    id: str = Field(default=None, alias="_id")
    project_id: str
    thread_id: str
    title: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: datetime = Field(default_factory=datetime.utcnow)

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

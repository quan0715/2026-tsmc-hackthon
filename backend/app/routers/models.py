"""Models API - 提供可用模型清單"""
from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/models", tags=["models"])


class ModelInfo(BaseModel):
    id: str
    display_name: str
    description: str
    context_window: Optional[int] = None


@router.get("", response_model=List[ModelInfo])
async def list_available_models():
    """取得所有可用的 LLM 模型"""
    try:
        from agent.model_config import list_available_models
        models = list_available_models()
        return [ModelInfo(**m) for m in models]
    except Exception:
        return [
            ModelInfo(
                id="claude-haiku-4-5",
                display_name="Claude Haiku 4.5",
                description="快速且經濟的模型",
                context_window=200000,
            )
        ]

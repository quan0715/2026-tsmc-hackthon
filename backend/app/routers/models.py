"""Models API - 提供可用模型清單

NOTE: 模型列表同時定義在 agent/model_config.py（容器內使用）。
新增或修改模型時，兩處需同步更新。
"""
from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel

from ..config import settings

router = APIRouter(prefix="/api/v1/models", tags=["models"])


class ModelInfo(BaseModel):
    id: str
    display_name: str
    provider: str
    description: str
    context_window: Optional[int] = None


# provider ID → 需要哪些 credentials
ANTHROPIC_MODELS = [
    ModelInfo(id="claude-haiku-4-5", display_name="Claude Haiku 4.5", provider="Anthropic",
             description="最快速且經濟的模型，適合簡單任務", context_window=200000),
    ModelInfo(id="claude-sonnet-4-5", display_name="Claude Sonnet 4.5", provider="Anthropic",
             description="平衡效能與成本，適合大多數任務", context_window=200000),
    ModelInfo(id="claude-opus-4-6", display_name="Claude Opus 4.6", provider="Anthropic",
             description="最強大的模型，適合複雜推理任務", context_window=200000),
]

VERTEX_MODELS = [
    ModelInfo(id="claude-sonnet-vertex", display_name="Claude Sonnet 4.5 (Vertex)", provider="Vertex AI",
             description="透過 Vertex AI 使用 Claude Sonnet", context_window=200000),
    ModelInfo(id="gemini-2-5-pro", display_name="Gemini 2.5 Pro", provider="Vertex AI",
             description="Google 強大模型，擅長推理與創意任務", context_window=1000000),
    ModelInfo(id="gemini-3-pro-preview", display_name="Gemini 3 Pro Preview", provider="Vertex AI",
             description="Gemini 下一代模型預覽版", context_window=1000000),
    ModelInfo(id="deepseek-v3-1", display_name="DeepSeek V3.1", provider="Vertex AI",
             description="DeepSeek 高效能推理模型，擅長程式碼理解", context_window=128000),
    ModelInfo(id="deepseek-r1", display_name="DeepSeek R1 (0528)", provider="Vertex AI",
             description="DeepSeek 推理增強版本，適合複雜邏輯任務", context_window=128000),
    ModelInfo(id="qwen3-next-80b", display_name="Qwen3 Next 80B Thinking", provider="Vertex AI",
             description="Qwen3 思考增強模型，適合深度推理", context_window=32768),
    ModelInfo(id="qwen3-coder-480b", display_name="Qwen3 Coder 480B", provider="Vertex AI",
             description="Qwen3 超大規模程式碼專用模型", context_window=32768),
    ModelInfo(id="llama-4-maverick", display_name="Llama 4 Maverick", provider="Vertex AI",
             description="Meta Llama 4 輕量高效模型", context_window=128000),
    ModelInfo(id="gpt-oss-120b", display_name="GPT OSS 120B", provider="Vertex AI",
             description="開源 GPT 架構大型模型", context_window=8192),
    ModelInfo(id="gpt-oss-20b", display_name="GPT OSS 20B", provider="Vertex AI",
             description="開源 GPT 架構輕量模型", context_window=8192),
]


@router.get("", response_model=List[ModelInfo])
async def list_available_models():
    """取得可用的 LLM 模型（根據環境配置過濾）"""
    models: List[ModelInfo] = []

    if settings.anthropic_api_key:
        models.extend(ANTHROPIC_MODELS)

    has_vertex = bool(settings.gcp_project_id and settings.google_application_credentials)
    if has_vertex:
        models.extend(VERTEX_MODELS)

    return models

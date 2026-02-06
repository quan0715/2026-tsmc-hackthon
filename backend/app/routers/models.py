"""Models API - 提供可用模型清單

NOTE: 模型列表同時定義在 agent/model_config.py（容器內使用）。
新增或修改模型時，兩處需同步更新。
"""
from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/models", tags=["models"])


class ModelInfo(BaseModel):
    id: str
    display_name: str
    description: str
    context_window: Optional[int] = None


AVAILABLE_MODELS: List[ModelInfo] = [
    # Anthropic API
    ModelInfo(id="claude-haiku-4-5", display_name="Claude Haiku 4.5",
             description="最快速且經濟的模型，適合簡單任務", context_window=200000),
    ModelInfo(id="claude-sonnet-4-5", display_name="Claude Sonnet 4.5",
             description="平衡效能與成本，適合大多數任務", context_window=200000),
    ModelInfo(id="claude-opus-4-6", display_name="Claude Opus 4.6",
             description="最強大的模型，適合複雜推理任務", context_window=200000),
    # Vertex AI - Anthropic
    ModelInfo(id="claude-sonnet-vertex", display_name="Claude Sonnet 4.5 (Vertex AI)",
             description="透過 Vertex AI 使用 Claude Sonnet", context_window=200000),
    # Vertex AI - Gemini
    ModelInfo(id="gemini-2-5-pro", display_name="Gemini 2.5 Pro",
             description="Google 強大模型，擅長推理與創意任務", context_window=1000000),
    ModelInfo(id="gemini-3-pro-preview", display_name="Gemini 3 Pro Preview",
             description="Gemini 下一代模型預覽版，最新功能搶先體驗", context_window=1000000),
    # Vertex AI - DeepSeek
    ModelInfo(id="deepseek-v3-1", display_name="DeepSeek V3.1",
             description="DeepSeek 高效能推理模型，擅長程式碼理解", context_window=128000),
    ModelInfo(id="deepseek-r1", display_name="DeepSeek R1 (0528)",
             description="DeepSeek 推理增強版本，適合複雜邏輯任務", context_window=128000),
    # Vertex AI - Qwen
    ModelInfo(id="qwen3-next-80b", display_name="Qwen3 Next 80B Thinking",
             description="Qwen3 思考增強模型，適合需要深度推理的任務", context_window=32768),
    ModelInfo(id="qwen3-coder-480b", display_name="Qwen3 Coder 480B",
             description="Qwen3 超大規模程式碼專用模型，頂級程式碼生成能力", context_window=32768),
    # Vertex AI - Llama
    ModelInfo(id="llama-4-maverick", display_name="Llama 4 Maverick",
             description="Meta Llama 4 輕量高效模型，平衡速度與能力", context_window=128000),
    # Vertex AI - OpenAI OSS
    ModelInfo(id="gpt-oss-120b", display_name="GPT OSS 120B",
             description="開源 GPT 架構大型模型，通用任務表現優異", context_window=8192),
    ModelInfo(id="gpt-oss-20b", display_name="GPT OSS 20B",
             description="開源 GPT 架構輕量模型，快速響應", context_window=8192),
]


@router.get("", response_model=List[ModelInfo])
async def list_available_models():
    """取得所有可用的 LLM 模型"""
    return AVAILABLE_MODELS

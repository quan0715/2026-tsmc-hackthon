"""模型配置 - 定義所有可用的 LLM 模型"""

AVAILABLE_MODELS = {
    # ==================== Anthropic API (直接) ====================
    "claude-haiku-4-5": {
        "display_name": "Claude Haiku 4.5",
        "provider": "anthropic",
        "model_name": "claude-haiku-4-5-20251001",
        "description": "最快速且經濟的模型，適合簡單任務",
        "context_window": 200000,
    },
    "claude-sonnet-4-5": {
        "display_name": "Claude Sonnet 4.5",
        "provider": "anthropic",
        "model_name": "claude-sonnet-4-5-20250929",
        "description": "平衡效能與成本，適合大多數任務",
        "context_window": 200000,
    },
    # ==================== Vertex AI - Anthropic ====================
    "claude-sonnet-vertex": {
        "display_name": "Claude Sonnet 4.5 (Vertex AI)",
        "provider": "vertex-anthropic",
        "model_name": "claude-sonnet-4-5",
        "location": "us-east5",
        "description": "透過 Vertex AI 使用 Claude Sonnet",
        "context_window": 200000,
    },

    # ==================== Vertex AI - Gemini ====================
    "gemini-2-5-pro": {
        "display_name": "Gemini 2.5 Pro",
        "provider": "vertex-gemini",
        "model_name": "gemini-2.5-pro",
        "location": "us-central1",
        "description": "Google 強大模型，擅長推理與創意任務",
        "context_window": 1000000,
    },
    "gemini-3-pro-preview": {
        "display_name": "Gemini 3 Pro Preview",
        "provider": "vertex-gemini",
        "model_name": "gemini-3-pro-preview",
        "location": "global",
        "description": "Gemini 下一代模型預覽版，最新功能搶先體驗",
        "context_window": 1000000,
    },

    # ==================== Vertex AI - DeepSeek ====================
    "deepseek-v3-1": {
        "display_name": "DeepSeek V3.1",
        "provider": "vertex-other",
        "model_name": "deepseek-ai/deepseek-v3.1-maas",
        "location": "us-west2",
        "description": "DeepSeek 高效能推理模型，擅長程式碼理解",
        "context_window": 128000,
    },
    "deepseek-r1": {
        "display_name": "DeepSeek R1 (0528)",
        "provider": "vertex-other",
        "model_name": "deepseek-ai/deepseek-r1-0528-maas",
        "location": "us-central1",
        "description": "DeepSeek 推理增強版本，適合複雜邏輯任務",
        "context_window": 128000,
    },

    # ==================== Vertex AI - Qwen ====================
    "qwen3-next-80b": {
        "display_name": "Qwen3 Next 80B Thinking",
        "provider": "vertex-other",
        "model_name": "qwen/qwen3-next-80b-a3b-thinking-maas",
        "location": "global",
        "description": "Qwen3 思考增強模型，適合需要深度推理的任務",
        "context_window": 32768,
    },
    "qwen3-coder-480b": {
        "display_name": "Qwen3 Coder 480B",
        "provider": "vertex-other",
        "model_name": "qwen/qwen3-coder-480b-a35b-instruct-maas",
        "location": "us-south1",
        "description": "Qwen3 超大規模程式碼專用模型，頂級程式碼生成能力",
        "context_window": 32768,
    },

    # ==================== Vertex AI - Llama ====================
    "llama-4-maverick": {
        "display_name": "Llama 4 Maverick",
        "provider": "vertex-other",
        "model_name": "meta/llama-4-maverick-17b-128e-instruct-maas",
        "location": "us-east5",
        "description": "Meta Llama 4 輕量高效模型，平衡速度與能力",
        "context_window": 128000,
    },

    # ==================== Vertex AI - OpenAI OSS ====================
    "gpt-oss-120b": {
        "display_name": "GPT OSS 120B",
        "provider": "vertex-other",
        "model_name": "openai/gpt-oss-120b-maas",
        "location": "us-central1",
        "description": "開源 GPT 架構大型模型，通用任務表現優異",
        "context_window": 8192,
    },
    "gpt-oss-20b": {
        "display_name": "GPT OSS 20B",
        "provider": "vertex-other",
        "model_name": "openai/gpt-oss-20b-maas",
        "location": "us-central1",
        "description": "開源 GPT 架構輕量模型，快速響應",
        "context_window": 8192,
    },
}

DEFAULT_MODEL = "claude-haiku-4-5"


def get_model_config(model_id: str) -> dict:
    """取得模型配置"""
    if model_id not in AVAILABLE_MODELS:
        raise ValueError(f"未知的模型: {model_id}")
    return AVAILABLE_MODELS[model_id]


def list_available_models() -> list:
    """列出所有可用模型"""
    return [
        {
            "id": model_id,
            "display_name": config["display_name"],
            "description": config["description"],
            "context_window": config.get("context_window"),
        }
        for model_id, config in AVAILABLE_MODELS.items()
    ]

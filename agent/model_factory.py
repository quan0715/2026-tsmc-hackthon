"""模型工廠 - 根據模型 ID 動態建立 LLM 實例"""
import os
import logging
from typing import Optional

from agent.model_config import get_model_config, DEFAULT_MODEL
from agent.models import AnthropicModelProvider, VertexModelProvider

logger = logging.getLogger(__name__)


class ModelFactory:
    """多 Provider 模型工廠"""

    def __init__(self):
        # 初始化 Anthropic Provider
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        self.anthropic_provider = (
            AnthropicModelProvider(api_key=anthropic_key) if anthropic_key else None
        )

        # 初始化 Vertex AI Provider
        gcp_project = os.getenv("GCP_PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")

        if gcp_project:
            try:
                self.vertex_provider = VertexModelProvider(project=gcp_project)
            except Exception as e:
                logger.warning(f"Vertex AI Provider 初始化失敗: {e}")
                self.vertex_provider = None
        else:
            self.vertex_provider = None

        logger.info(
            f"ModelFactory 已初始化 "
            f"(anthropic={'yes' if self.anthropic_provider else 'no'}, "
            f"vertex={'yes' if self.vertex_provider else 'no'})"
        )

    def create_model(self, model_id: Optional[str] = None):
        """根據模型 ID 建立 LLM 實例

        Args:
            model_id: 模型 ID (e.g., "claude-haiku-4-5", "gemini-2-5-pro")

        Returns:
            LLM 實例

        Raises:
            ValueError: 如果模型不存在或 provider 未配置
        """
        if not model_id:
            model_id = DEFAULT_MODEL

        config = get_model_config(model_id)
        provider = config["provider"]
        model_name = config["model_name"]

        logger.info(f"建立模型: {model_id} (provider={provider}, model={model_name})")

        if provider == "anthropic":
            if not self.anthropic_provider:
                raise ValueError(
                    "Anthropic API 未配置。請設定 ANTHROPIC_API_KEY 環境變數"
                )
            return self.anthropic_provider.get_model(model_name=model_name)

        elif provider == "vertex-anthropic":
            if not self.vertex_provider:
                raise ValueError(
                    "Vertex AI 未配置。請設定 GCP_PROJECT_ID 並確保 "
                    "ADC 或 GOOGLE_APPLICATION_CREDENTIALS 可用"
                )
            location = config.get("location", "us-east5")
            return self.vertex_provider.get_anthropic_vertex_model(
                model_name=model_name, location=location
            )

        elif provider == "vertex-gemini":
            if not self.vertex_provider:
                raise ValueError(
                    "Vertex AI 未配置。請設定 GCP_PROJECT_ID 並確保 "
                    "ADC 或 GOOGLE_APPLICATION_CREDENTIALS 可用"
                )
            location = config.get("location", "us-central1")
            return self.vertex_provider.get_gemini_vertex_model(
                model_name=model_name, location=location
            )

        elif provider == "vertex-other":
            if not self.vertex_provider:
                raise ValueError(
                    "Vertex AI 未配置。請設定 GCP_PROJECT_ID 並確保 "
                    "ADC 或 GOOGLE_APPLICATION_CREDENTIALS 可用"
                )
            location = config.get("location", "us-central1")
            return self.vertex_provider.get_vertex_model(
                model_name=model_name, location=location
            )

        else:
            raise ValueError(f"未知的 provider: {provider}")

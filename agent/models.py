import os
from langchain.messages import (
    AIMessage,
    AIMessageChunk,
    HumanMessage,
    SystemMessage,
)
from langchain_core.outputs import LLMResult
from langchain_anthropic import ChatAnthropic

# Vertex AI 相關套件使用條件 import（避免依賴衝突）
try:
    import google.auth
    from langchain_google_vertexai.model_garden import ChatAnthropicVertex
    from langchain_google_genai import ChatGoogleGenerativeAI
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

DEFAULT_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "")
DEFAULT_LOCATION = os.getenv("GCP_LOCATION", "us-central1")


class VertexModelProvider:
    def __init__(self, project: str = None):
        if not VERTEX_AI_AVAILABLE:
            raise ImportError(
                "Vertex AI dependencies not available. "
                "Install with: pip install langchain-google-vertexai langchain-google-genai"
            )
        self.project = project or DEFAULT_PROJECT_ID
        if not self.project:
            raise ValueError("GCP_PROJECT_ID is required for Vertex AI")
        self.credentials = self._load_credentials()

    def _load_credentials(self):
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]
        try:
            creds, _ = google.auth.default(scopes=scopes)
        except Exception as exc:
            raise ValueError("ADC credentials not available") from exc
        if creds is None:
            raise ValueError("ADC credentials not available")
        return creds

    def get_anthropic_vertex_model(
        self,
        model_name: str = "claude-sonnet-4-5",
        location: str = "us-east5",
    ):
        """取得 Anthropic Vertex AI 模型"""
        return ChatAnthropicVertex(
            project=self.project,
            location=location,
            model_name=model_name,
            credentials=self.credentials,
        )

    def get_gemini_vertex_model(
        self,
        model_name: str = "gemini-2.5-pro",
        location: str = DEFAULT_LOCATION,
    ):
        """取得 Gemini Vertex AI 模型"""
        return ChatGoogleGenerativeAI(
            project=self.project,
            location=location,
            model=model_name,
            vertexai=True,
            temperature=0.7,
            max_output_tokens=8000,
            top_p=0.95,
            credentials=self.credentials,
        )

    def get_vertex_model(
        self,
        model_name: str,
        location: str = DEFAULT_LOCATION,
    ):
        """取得 Vertex AI Model Garden 中的通用模型

        支援：DeepSeek, Qwen, Llama, GPT OSS 等第三方模型
        """
        return ChatGoogleGenerativeAI(
            project=self.project,
            location=location,
            model=model_name,
            vertexai=True,
            temperature=0.7,
            max_output_tokens=8000,
            top_p=0.95,
            credentials=self.credentials,
        )


class AnthropicModelProvider:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if self.api_key is None:
            raise ValueError("ANTHROPIC_API_KEY is not set")

    def get_model(self, model_name: str = "claude-haiku-4-5-20251001"):
        """取得 Anthropic 模型"""
        return ChatAnthropic(
            model=model_name,
            api_key=self.api_key,
        )


if __name__ == "__main__":
    # test anthropic model
    anthropic_model_provider = AnthropicModelProvider()
    context_model = anthropic_model_provider.get_model()
    # 移除註解可以測試 vertex model 的連接
    # vertex_model_provider = VertexModelProvider(project=DEFAULT_PROJECT_ID)
    # context_model = vertex_model_provider.get_gemini_vertex_model()
    result = context_model.stream(
        [
            SystemMessage(content="你是Quan的 Coding 助理，幫忙處理coding相關的問題"),
            HumanMessage(content="請幫我寫一個Hello World的程式，C++語言"),
        ],
    )
    for chunk in result:
        print(chunk.content, end="", flush=True)

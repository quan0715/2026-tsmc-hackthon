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
    from google.oauth2.service_account import Credentials
    from langchain_google_vertexai.model_garden import ChatAnthropicVertex
    from langchain_google_genai import ChatGoogleGenerativeAI
    VERTEX_AI_AVAILABLE = True
except ImportError:
    VERTEX_AI_AVAILABLE = False

PROJECT_ID = "cloud-native-458808"
CREDENTIALS_PATH = "cloud-native-458808-f41aa4273928.json"


class VertexModelProvider:
    def __init__(self, project: str, credentials_path: str):
        if not VERTEX_AI_AVAILABLE:
            raise ImportError(
                "Vertex AI dependencies not available. "
                "Install with: pip install langchain-google-vertexai langchain-google-genai"
            )
        self.credentials = self._load_credentials(credentials_path)
        self.project = project

    def _load_credentials(self, credentials_path: str):
        try:
            return Credentials.from_service_account_file(
                credentials_path,
                scopes=["https://www.googleapis.com/auth/cloud-platform"],
            )
        except FileNotFoundError:
            raise ValueError("credentials.json file not found")

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
        location: str = "us-central1",
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
        location: str = "us-central1",
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
    # vertex_model_provider = VertexModelProvider(
    #     project=PROJECT_ID, credentials_path=CREDENTIALS_PATH)
    # context_model = vertex_model_provider.get_gemini_vertex_model()
    result = context_model.stream(
        [
            SystemMessage(content="你是Quan的 Coding 助理，幫忙處理coding相關的問題"),
            HumanMessage(content="請幫我寫一個Hello World的程式，C++語言"),
        ],
    )
    for chunk in result:
        print(chunk.content, end="", flush=True)

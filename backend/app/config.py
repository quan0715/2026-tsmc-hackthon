"""應用程式配置管理"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """應用程式設定"""

    # API 設定
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 1
    debug: bool = False

    # MongoDB 設定
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_database: str = "refactor_agent"

    # PostgreSQL 設定（LangGraph 持久化 - 必填！）
    # ⚠️ Agent 無法在沒有 PostgreSQL 的情況下運行
    postgres_url: str

    # Docker 設定
    docker_base_image: str = "refactor-base:latest"
    docker_network: str = "refactor-network"
    docker_volume_prefix: str = "/tmp/refactor-workspaces"

    # 容器資源限制
    container_cpu_limit: float = 2.0
    container_memory_limit: str = "2g"

    # Git 設定
    git_clone_timeout: int = 300
    git_depth: int = 1

    # Log 設定
    log_level: str = "INFO"

    # JWT 認證設定
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_hours: int = 24

    # LLM 設定 - Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-5-20250929"

    # Vertex AI 設定
    gcp_project_id: str = ""
    gcp_location: str = "us-central1"
    vertex_ai_model: str = "gemini-2.5-pro"
    google_application_credentials: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False


# 全域設定實例
settings = Settings()

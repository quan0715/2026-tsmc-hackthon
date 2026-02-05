"""應用程式配置管理"""
import secrets
import logging
from pydantic_settings import BaseSettings
from typing import Optional

logger = logging.getLogger(__name__)

# 生成一個安全的隨機 fallback secret（每次啟動時不同）
_DEFAULT_JWT_SECRET = secrets.token_urlsafe(32)


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

    # PostgreSQL 設定（LangGraph 持久化，可選）
    postgres_url: Optional[str] = None

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
    # 注意：如果未設定 JWT_SECRET_KEY 環境變數，將使用隨機生成的 key
    # 這會導致每次重啟服務後所有 token 失效
    jwt_secret_key: str = _DEFAULT_JWT_SECRET
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

# 檢查 JWT secret key 是否使用預設值（警告）
if settings.jwt_secret_key == _DEFAULT_JWT_SECRET:
    logger.warning(
        "⚠️  JWT_SECRET_KEY 未設定，使用隨機生成的 key。"
        "這會導致每次重啟服務後所有 token 失效。"
        "請在生產環境設定 JWT_SECRET_KEY 環境變數。"
    )

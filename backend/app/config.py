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

    class Config:
        env_file = ".env"
        case_sensitive = False


# 全域設定實例
settings = Settings()

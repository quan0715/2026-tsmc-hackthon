"""測試配置"""
import pytest
import os
from pymongo import AsyncMongoClient
from httpx import AsyncClient
from app.config import settings
from app.main import app
from app.services.auth_service import AuthService
from app.services.project_service import ProjectService
from app.services.chat_session_service import ChatSessionService
from typing import AsyncGenerator


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """設置測試資料庫"""
    # 使用測試資料庫和本地 MongoDB
    settings.mongodb_url = "mongodb://localhost:27017"
    settings.mongodb_database = "refactor_agent_test"

    # 在測試後清理
    yield

    # 清理測試資料庫
    client = AsyncMongoClient(settings.mongodb_url)
    await client.drop_database(settings.mongodb_database)
    await client.close()


@pytest.fixture
async def db():
    """每個測試獨立的資料庫連接"""
    client = AsyncMongoClient(settings.mongodb_url)
    database = client[settings.mongodb_database]
    yield database
    await client.close()


@pytest.fixture
async def clean_db(db):
    """自動清理資料庫 fixture"""
    # 測試前清空所有 collections
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].delete_many({})

    yield db

    # 測試後清空
    collections = await db.list_collection_names()
    for collection in collections:
        await db[collection].delete_many({})


# ============ Service Layer Fixtures ============

@pytest.fixture
async def auth_service(clean_db) -> AuthService:
    """AuthService fixture"""
    return AuthService(clean_db)


@pytest.fixture
async def project_service(clean_db) -> ProjectService:
    """ProjectService fixture"""
    return ProjectService(clean_db)


@pytest.fixture
async def chat_session_service(clean_db) -> ChatSessionService:
    """ChatSessionService fixture"""
    return ChatSessionService(clean_db)


# ============ HTTP Client Fixtures ============

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """API 測試用 HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def test_user(auth_service: AuthService):
    """預先建立的測試用戶"""
    user = await auth_service.create_user(
        email="testuser@example.com",
        username="testuser",
        password="testpassword123"
    )
    return user


@pytest.fixture
async def auth_client(client: AsyncClient, auth_service: AuthService, test_user) -> AsyncClient:
    """帶有認證 token 的 client"""
    token, _ = auth_service.create_access_token(
        user_id=test_user.id,
        email=test_user.email
    )
    client.headers["Authorization"] = f"Bearer {token}"
    return client


# ============ Test Data Factory Fixtures ============

@pytest.fixture
def user_factory(auth_service: AuthService):
    """建立測試用戶的工廠函數"""
    async def _create_user(
        email: str = "factory@example.com",
        username: str = "factoryuser",
        password: str = "password123"
    ):
        return await auth_service.create_user(email, username, password)
    return _create_user


@pytest.fixture
def project_factory(project_service: ProjectService, test_user):
    """建立測試專案的工廠函數"""
    async def _create_project(
        title: str = "Test Project",
        repo_url: str = "https://github.com/test/repo.git",
        **kwargs
    ):
        return await project_service.create_project(
            title=title,
            repo_url=repo_url,
            owner_id=test_user.id,
            **kwargs
        )
    return _create_project


# ============ Mock Fixtures ============

@pytest.fixture
def mock_docker_subprocess(monkeypatch):
    """Mock subprocess.run for Docker commands"""
    from unittest.mock import MagicMock

    mock_run = MagicMock()
    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run


@pytest.fixture
def mock_httpx_client(monkeypatch):
    """Mock httpx.AsyncClient for AI Server calls"""
    from unittest.mock import AsyncMock

    mock_client = AsyncMock()
    monkeypatch.setattr("httpx.AsyncClient", mock_client)
    return mock_client


# ============ PostgreSQL Persistence Fixtures ============

@pytest.fixture
def test_postgres_url():
    """提供測試用 PostgreSQL URL"""
    return os.environ.get(
        "POSTGRES_URL",
        "postgresql://langgraph:langgraph_secret@localhost:5432/langgraph"
    )


@pytest.fixture
async def refactor_agent_with_postgres(test_postgres_url):
    """建立使用 PostgreSQL 的 RefactorAgent 實例"""
    from agent.deep_agent import RefactorAgent
    from agent.models import AnthropicModelProvider

    provider = AnthropicModelProvider()
    model = provider.get_model()

    agent = RefactorAgent(
        model=model,
        postgres_url=test_postgres_url,
        verbose=False,
    )

    yield agent

    # 清理：可選擇清理測試產生的 checkpoints
    # 注意：由於 PostgreSQL 是共享的，這裡暫時不實作清理邏輯
    # 實際生產環境應使用獨立的測試資料庫

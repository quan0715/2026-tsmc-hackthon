"""測試配置"""
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """設置測試資料庫"""
    # 使用測試資料庫
    settings.mongodb_database = "refactor_agent_test"

    # 在測試後清理
    yield

    # 清理測試資料庫
    client = AsyncIOMotorClient(settings.mongodb_url)
    await client.drop_database(settings.mongodb_database)
    client.close()

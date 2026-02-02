"""MongoDB 連接管理"""
from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase
from typing import Optional
from ..config import settings
import logging

logger = logging.getLogger(__name__)


class MongoDB:
    """MongoDB 連接管理器"""

    client: Optional[AsyncMongoClient] = None
    database: Optional[AsyncDatabase] = None

    async def connect(self):
        """建立 MongoDB 連接"""
        try:
            self.client = AsyncMongoClient(settings.mongodb_url)
            self.database = self.client[settings.mongodb_database]
            # 測試連接
            await self.client.admin.command("ping")
            logger.info(f"成功連接到 MongoDB: {settings.mongodb_database}")
        except Exception as e:
            logger.error(f"MongoDB 連接失敗: {e}")
            raise

    async def disconnect(self):
        """關閉 MongoDB 連接"""
        if self.client:
            await self.client.close()
            logger.info("MongoDB 連接已關閉")

    def get_database(self) -> AsyncDatabase:
        """獲取資料庫實例"""
        if self.database is None:
            raise RuntimeError("資料庫未初始化")
        return self.database


# 全域資料庫實例
mongodb = MongoDB()


def get_database() -> AsyncDatabase:
    """依賴注入：獲取資料庫實例"""
    return mongodb.get_database()

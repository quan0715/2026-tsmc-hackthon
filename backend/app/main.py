"""FastAPI 應用程式入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database.mongodb import mongodb
from .routers import health, projects

# 配置日誌
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時執行
    logger.info("正在啟動應用程式...")
    await mongodb.connect()
    logger.info("應用程式啟動完成")

    yield

    # 關閉時執行
    logger.info("正在關閉應用程式...")
    await mongodb.disconnect()
    logger.info("應用程式已關閉")


# 建立 FastAPI 應用
app = FastAPI(
    title="AI 舊程式碼智能重構系統",
    description="提供隔離的 Docker 容器環境進行程式碼重構",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.debug,
)

# CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應該限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(health.router)
app.include_router(projects.router)

# 根路徑
@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "AI 舊程式碼智能重構系統 API",
        "version": "0.1.0",
        "docs": "/docs",
    }

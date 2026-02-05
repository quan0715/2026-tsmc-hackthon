"""FastAPI 應用程式入口"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .config import settings
from .database.mongodb import mongodb
from .routers import health, projects, auth, agent, chat

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
# 從環境變數讀取允許的來源，生產環境應設定具體域名
cors_origins = os.environ.get("CORS_ORIGINS", "").split(",")
# 如果未設定，開發模式允許所有來源，生產模式僅允許本地
if not cors_origins or cors_origins == [""]:
    if settings.debug:
        cors_origins = ["*"]
    else:
        cors_origins = ["http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

# 註冊路由
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(agent.router)
app.include_router(chat.router)

# 根路徑
@app.get("/")
async def root():
    """根路徑"""
    return {
        "message": "AI 舊程式碼智能重構系統 API",
        "version": "0.1.0",
        "docs": "/docs",
    }

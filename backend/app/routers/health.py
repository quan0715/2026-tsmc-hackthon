"""健康檢查路由"""
from fastapi import APIRouter, Depends
from pymongo.asynchronous.database import AsyncDatabase
from ..database.mongodb import get_database
from datetime import datetime

router = APIRouter(prefix="/api/v1", tags=["health"])


@router.get("/health")
def health_check(db: AsyncDatabase = Depends(get_database)):
    """健康檢查端點"""
    try:
        # 測試資料庫連接
        db.command("ping")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
    }

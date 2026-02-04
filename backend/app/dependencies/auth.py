"""認證依賴注入"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo.asynchronous.database import AsyncDatabase

from ..models.user import User
from ..services.auth_service import AuthService
from ..database.mongodb import get_database


# HTTP Bearer Token 認證方案
security = HTTPBearer()


def get_auth_service(db: AsyncDatabase = Depends(get_database)) -> AuthService:
    """獲取認證服務實例"""
    return AuthService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    """
    獲取當前用戶（需要認證）

    從 Authorization Header 中解析 JWT Token，驗證並返回用戶資訊

    Raises:
        HTTPException: 401 if token is invalid or user not found
    """
    token = credentials.credentials

    try:
        # 解碼 token
        payload = auth_service.decode_token(token)
        user_id: str = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 從資料庫查詢用戶
    user = await auth_service.get_user_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )

    return user


async def verify_project_access(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncDatabase = Depends(get_database),
):
    """
    驗證專案存在且用戶有權限訪問
    
    Returns:
        Project: 專案物件
        
    Raises:
        HTTPException: 404 if project not found, 403 if no permission
    """
    from ..services.project_service import ProjectService
    
    service = ProjectService(db)
    project = await service.get_project_by_id(project_id)
    
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="專案不存在"
        )
    
    if project.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="無權限訪問此專案"
        )
    
    return project

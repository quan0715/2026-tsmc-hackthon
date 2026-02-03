"""專案路由"""
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo.asynchronous.database import AsyncDatabase

from ..database.mongodb import get_database
from ..services.project_service import ProjectService
from ..models.project import ProjectStatus
from ..models.user import User
from ..dependencies.auth import get_current_user, verify_project_access
from ..schemas.project import (
    CreateProjectRequest,
    UpdateProjectRequest,
    ProjectResponse,
    ProjectListResponse,
)
from ..schemas.provision import ProvisionResponse
from ..schemas.execution import ExecCommandRequest, ExecCommandResponse
from ..services.container_service import ContainerService
from ..services.log_service import LogService
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])
logger = logging.getLogger(__name__)


async def get_project_service(
    db: AsyncDatabase = Depends(get_database),
) -> ProjectService:
    """依賴注入：獲取專案服務"""
    return ProjectService(db)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: CreateProjectRequest,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user),
):
    """建立專案（需要認證）"""
    project = await service.create_project(
        request,
        owner_id=current_user.id,
        owner_email=current_user.email
    )
    return ProjectResponse(**project.model_dump(by_alias=True))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    include_docker_status: bool = True,
    service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """查詢專案（包含 Docker 狀態和一致性檢查，需要認證）"""
    if include_docker_status:
        project_data = await service.get_project_with_docker_status(project_id)
        return ProjectResponse(**project_data)
    else:
        return ProjectResponse(**project.model_dump(by_alias=True))


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    request: UpdateProjectRequest,
    service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """更新專案（需要認證，Provision 後不能修改 repo_url）"""
    # 如果專案已經 provision（狀態不是 CREATED），則不允許修改 repo_url
    if project.status != ProjectStatus.CREATED and request.repo_url is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="專案已經 Provision，無法修改 Repository URL"
        )

    # 執行更新
    updated_project = await service.update_project(project_id, request)
    if not updated_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="更新失敗"
        )

    return ProjectResponse(**updated_project.model_dump(by_alias=True))


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    service: ProjectService = Depends(get_project_service),
    current_user: User = Depends(get_current_user),
):
    """列出當前用戶的所有專案（需要認證）"""
    projects, total = await service.list_projects(
        skip=skip, limit=limit, owner_id=current_user.id
    )
    return ProjectListResponse(
        total=total,
        projects=[
            ProjectResponse(**p.model_dump(by_alias=True)) for p in projects
        ],
    )


@router.post("/{project_id}/provision", response_model=ProvisionResponse)
async def provision_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """Provision 專案 - 建立容器並 clone repository（需要認證）"""
    try:
        project = await service.provision_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="專案不存在"
            )

        return ProvisionResponse(
            message="專案 provision 成功",
            project_id=project.id,
            container_id=project.container_id,
            status=project.status,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Provision 失敗: {str(e)}",
        )


@router.post("/{project_id}/exec", response_model=ExecCommandResponse)
async def exec_command(
    project_id: str,
    request: ExecCommandRequest,
    service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """在專案容器中執行指令（需要認證）"""
    # 檢查容器是否存在
    if not project.container_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="專案尚未 provision,請先執行 provision",
        )

    # 執行指令
    try:
        container_service = ContainerService()
        result = container_service.exec_command(
            project.container_id, request.command, request.workdir
        )
        return ExecCommandResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"執行指令失敗: {str(e)}",
        )


@router.get("/{project_id}/logs/stream")
async def stream_logs(
    project_id: str,
    follow: bool = True,
    tail: int = 100,
    service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """串流容器日誌 (SSE)（需要認證）"""
    # 檢查容器是否存在
    if not project.container_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="專案尚未 provision,請先執行 provision",
        )

    # 串流日誌
    log_service = LogService()
    return EventSourceResponse(
        log_service.stream_container_logs(
            project.container_id, follow=follow, tail=tail
        )
    )


@router.post("/{project_id}/stop", response_model=ProjectResponse)
async def stop_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """停止專案容器（需要認證）"""
    try:
        project = await service.stop_project(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="專案不存在"
            )
        return ProjectResponse(**project.model_dump(by_alias=True))
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"停止專案失敗: {str(e)}",
        )


@router.post("/{project_id}/reprovision", response_model=ProjectResponse)
async def reprovision_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """重設專案（刪除容器並重新 provision）"""
    try:
        # 先停止並刪除現有容器（如果存在）
        if project.container_id:
            container_service = ContainerService()
            container_service.stop_container(project.container_id)
            container_service.remove_container(project.container_id)

            # 清除容器 ID 並重設狀態
            await service.update_project(
                project_id,
                UpdateProjectRequest(
                    container_id=None,
                    status=ProjectStatus.CREATED
                )
            )

        # 重新 provision
        updated_project = await service.provision_project(project_id)
        return ProjectResponse(**updated_project.model_dump(by_alias=True))

    except Exception as e:
        logger.error(f"重設專案失敗: project_id={project_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重設專案失敗: {str(e)}",
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
    project = Depends(verify_project_access),
):
    """刪除專案和容器（需要認證）"""
    success = await service.delete_project(project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="專案不存在"
        )

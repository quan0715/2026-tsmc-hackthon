"""專案路由"""
from fastapi import APIRouter, Depends, HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..database.mongodb import get_database
from ..services.project_service import ProjectService
from ..schemas.project import (
    CreateProjectRequest,
    ProjectResponse,
    ProjectListResponse,
)
from ..schemas.provision import ProvisionResponse
from ..schemas.execution import ExecCommandRequest, ExecCommandResponse
from ..services.container_service import ContainerService
from ..services.log_service import LogService
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])


def get_project_service(
    db: AsyncIOMotorDatabase = Depends(get_database),
) -> ProjectService:
    """依賴注入：獲取專案服務"""
    return ProjectService(db)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: CreateProjectRequest,
    service: ProjectService = Depends(get_project_service),
):
    """建立專案"""
    project = await service.create_project(request)
    return ProjectResponse(**project.model_dump(by_alias=True))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    include_docker_status: bool = True,
    service: ProjectService = Depends(get_project_service),
):
    """查詢專案（包含 Docker 狀態和一致性檢查）"""
    if include_docker_status:
        project_data = await service.get_project_with_docker_status(project_id)
        if not project_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="專案不存在"
            )
        return ProjectResponse(**project_data)
    else:
        project = await service.get_project_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="專案不存在"
            )
        return ProjectResponse(**project.model_dump(by_alias=True))


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    service: ProjectService = Depends(get_project_service),
):
    """列出所有專案"""
    projects, total = await service.list_projects(skip=skip, limit=limit)
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
):
    """Provision 專案 - 建立容器並 clone repository"""
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
):
    """在專案容器中執行指令"""
    # 查詢專案
    project = await service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="專案不存在"
        )

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
):
    """串流容器日誌 (SSE)"""
    # 查詢專案
    project = await service.get_project_by_id(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="專案不存在"
        )

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
):
    """停止專案容器"""
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


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service),
):
    """刪除專案和容器"""
    success = await service.delete_project(project_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="專案不存在"
        )

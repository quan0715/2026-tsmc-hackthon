"""專案服務層"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.project import Project, ProjectStatus
from ..schemas.project import CreateProjectRequest, UpdateProjectRequest
from .container_service import ContainerService
import logging

logger = logging.getLogger(__name__)


class ProjectService:
    """專案服務"""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.projects

    async def create_project(self, request: CreateProjectRequest) -> Project:
        """建立專案"""
        project = Project(
            repo_url=request.repo_url,
            branch=request.branch,
            init_prompt=request.init_prompt,
            status=ProjectStatus.CREATED,
        )

        # 轉換為字典並移除 id (由 MongoDB 自動生成)
        project_dict = project.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(project_dict)

        # 更新專案 ID
        project.id = str(result.inserted_id)
        return project

    async def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """根據 ID 查詢專案"""
        try:
            obj_id = ObjectId(project_id)
        except Exception:
            return None

        project_dict = await self.collection.find_one({"_id": obj_id})
        if not project_dict:
            return None

        # 轉換 ObjectId 為字串
        project_dict["_id"] = str(project_dict["_id"])
        return Project(**project_dict)

    async def get_project_with_docker_status(
        self, project_id: str
    ) -> Optional[dict]:
        """查詢專案並附加 Docker 容器狀態"""
        project = await self.get_project_by_id(project_id)
        if not project:
            return None

        result = project.model_dump(by_alias=True)

        # 如果有容器 ID，查詢 Docker 狀態
        if project.container_id:
            container_service = ContainerService()
            docker_status = container_service.get_container_status(project.container_id)

            if docker_status:
                result["docker_status"] = docker_status
            else:
                # 容器在 Docker 中不存在，但 DB 記錄存在 - 狀態不一致
                result["docker_status"] = {
                    "id": project.container_id[:12],
                    "status": "not_found",
                    "inconsistent": True,
                }
                logger.warning(
                    f"狀態不一致: 專案 {project_id} 的容器 {project.container_id} 在 Docker 中不存在"
                )
        else:
            result["docker_status"] = None

        return result

    async def list_projects(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[List[Project], int]:
        """列出所有專案"""
        # 查詢總數
        total = await self.collection.count_documents({})

        # 查詢專案列表
        cursor = self.collection.find().skip(skip).limit(limit).sort("created_at", -1)
        projects = []

        async for project_dict in cursor:
            project_dict["_id"] = str(project_dict["_id"])
            projects.append(Project(**project_dict))

        return projects, total

    async def update_project(
        self, project_id: str, update: UpdateProjectRequest
    ) -> Optional[Project]:
        """更新專案"""
        try:
            obj_id = ObjectId(project_id)
        except Exception:
            return None

        # 只更新提供的欄位
        update_dict = update.model_dump(exclude_unset=True)
        if not update_dict:
            return await self.get_project_by_id(project_id)

        # 更新時間
        update_dict["updated_at"] = datetime.utcnow()

        result = await self.collection.update_one(
            {"_id": obj_id}, {"$set": update_dict}
        )

        if result.matched_count == 0:
            return None

        return await self.get_project_by_id(project_id)

    async def stop_project(self, project_id: str) -> Optional[Project]:
        """停止專案容器"""
        container_service = ContainerService()

        # 獲取專案
        project = await self.get_project_by_id(project_id)
        if not project:
            return None

        # 檢查容器是否存在
        if not project.container_id:
            raise ValueError("專案尚未 provision,沒有容器可停止")

        try:
            # 停止容器
            container_service.stop_container(project.container_id)

            # 更新狀態為 STOPPED
            await self._update_project_status(project_id, ProjectStatus.STOPPED)

            logger.info(f"專案 {project_id} 已停止")
            return await self.get_project_by_id(project_id)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"停止專案失敗: {error_msg}")
            await self._update_project_status(
                project_id, ProjectStatus.FAILED, last_error=error_msg
            )
            raise

    async def delete_project(self, project_id: str) -> bool:
        """刪除專案和容器"""
        container_service = ContainerService()

        # 獲取專案
        project = await self.get_project_by_id(project_id)
        if not project:
            return False

        # 如果有容器,先刪除容器
        if project.container_id:
            try:
                container_service.remove_container(project.container_id, force=True)
                logger.info(f"已刪除容器: {project.container_id}")
            except Exception as e:
                logger.warning(f"刪除容器失敗: {e}")

        # 刪除資料庫記錄
        try:
            obj_id = ObjectId(project_id)
            result = await self.collection.delete_one({"_id": obj_id})

            if result.deleted_count > 0:
                logger.info(f"已刪除專案: {project_id}")
                return True
            return False
        except Exception:
            return False

    async def provision_project(self, project_id: str) -> Optional[Project]:
        """Provision 專案 - 建立容器並 clone repository"""
        container_service = ContainerService()

        # 獲取專案
        project = await self.get_project_by_id(project_id)
        if not project:
            return None

        # 檢查狀態
        if project.status != ProjectStatus.CREATED:
            raise ValueError(f"專案狀態必須為 CREATED,目前為 {project.status}")

        container_id = None
        try:
            # 更新狀態為 PROVISIONING
            await self._update_project_status(
                project_id, ProjectStatus.PROVISIONING, last_error=None
            )

            # 建立容器
            logger.info(f"建立容器: 專案 {project_id}")
            container = container_service.create_container(project_id)
            container_id = container["id"]

            # 啟動容器
            container_service.start_container(container_id)

            # Clone repository
            logger.info(f"Clone repository: {project.repo_url}")
            container_service.clone_repository(
                container_id,
                project.repo_url,
                project.branch,
            )

            # 更新專案狀態為 READY
            await self._update_project_status(
                project_id,
                ProjectStatus.READY,
                container_id=container_id,
                last_error=None,
            )

            logger.info(f"專案 {project_id} provision 完成")
            return await self.get_project_by_id(project_id)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Provision 失敗: {error_msg}")

            # 清理容器
            if container_id:
                try:
                    container_service.remove_container(container_id, force=True)
                except Exception as cleanup_error:
                    logger.error(f"清理容器失敗: {cleanup_error}")

            # 更新狀態為 FAILED
            await self._update_project_status(
                project_id, ProjectStatus.FAILED, last_error=error_msg
            )

            raise

    async def _update_project_status(
        self,
        project_id: str,
        status: ProjectStatus,
        container_id: str = None,
        last_error: str = None,
    ) -> None:
        """更新專案狀態"""
        try:
            obj_id = ObjectId(project_id)
        except Exception:
            return

        update_dict = {
            "status": status,
            "updated_at": datetime.utcnow(),
        }

        if container_id is not None:
            update_dict["container_id"] = container_id

        if last_error is not None:
            update_dict["last_error"] = last_error

        await self.collection.update_one({"_id": obj_id}, {"$set": update_dict})

"""專案服務層"""
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from pymongo.asynchronous.database import AsyncDatabase

from ..models.project import Project, ProjectStatus, ProjectType
from ..schemas.project import CreateProjectRequest, UpdateProjectRequest
from .container_service import ContainerService
from ..utils.mongodb_helpers import validate_and_convert_object_id, objectid_to_str
import logging

logger = logging.getLogger(__name__)


class ProjectService:
    """專案服務"""

    def __init__(self, db: AsyncDatabase):
        self.db = db
        self.collection = db.projects

    async def create_project(self, request: CreateProjectRequest, owner_id: str, owner_email: str = None) -> Project:
        """建立專案"""
        project = Project(
            title=request.title,
            description=request.description,
            project_type=request.project_type,
            repo_url=request.repo_url,
            branch=request.branch,
            spec=request.spec,
            status=ProjectStatus.CREATED,
            owner_id=owner_id,
            owner_email=owner_email,
        )

        # 轉換為字典並移除 id (由 MongoDB 自動生成)
        project_dict = project.model_dump(by_alias=True, exclude={"id"})
        result = await self.collection.insert_one(project_dict)

        # 更新專案 ID
        project.id = str(result.inserted_id)
        return project

    async def get_project_by_id(self, project_id: str) -> Optional[Project]:
        """根據 ID 查詢專案"""
        obj_id = validate_and_convert_object_id(project_id, "project_id")
        if not obj_id:
            return None

        project_dict = await self.collection.find_one({"_id": obj_id})
        if not project_dict:
            return None

        # 轉換 ObjectId 為字串
        objectid_to_str(project_dict)
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
        self, skip: int = 0, limit: int = 100, owner_id: Optional[str] = None
    ) -> tuple[List[Project], int]:
        """列出所有專案（可選擇過濾特定用戶的專案）"""
        # 建立查詢條件
        query = {}
        if owner_id:
            query["owner_id"] = owner_id

        # 查詢總數
        total = await self.collection.count_documents(query)

        # 查詢專案列表
        cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", -1)
        projects = []

        async for project_dict in cursor:
            project_dict["_id"] = str(project_dict["_id"])
            projects.append(Project(**project_dict))

        return projects, total

    async def update_project(
        self, project_id: str, update: UpdateProjectRequest | dict
    ) -> Optional[Project]:
        """更新專案

        Args:
            project_id: 專案 ID
            update: 更新內容，可以是 UpdateProjectRequest 或 dict
        """
        obj_id = validate_and_convert_object_id(project_id, "project_id")
        if not obj_id:
            return None

        # 只更新提供的欄位
        if isinstance(update, dict):
            # dict 直接使用，允許設置 None 值
            update_dict = update.copy()
        else:
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
        obj_id = validate_and_convert_object_id(project_id, "project_id")
        if not obj_id:
            return False

        try:
            result = await self.collection.delete_one({"_id": obj_id})

            if result.deleted_count > 0:
                logger.info(f"已刪除專案: {project_id}")
                return True
            return False
        except Exception:
            return False

    async def provision_project(
        self,
        project_id: str
    ) -> Optional[Project]:
        """Provision 專案 - 建立容器並 clone repository

        Args:
            project_id: 專案 ID
        """
        container_service = ContainerService()

        # 獲取專案
        project = await self.get_project_by_id(project_id)
        if not project:
            return None

        # 檢查狀態 - 允許 CREATED、STOPPED、FAILED 狀態重新 provision
        if project.status not in [ProjectStatus.CREATED, ProjectStatus.STOPPED, ProjectStatus.FAILED]:
            raise ValueError(
                f"專案狀態必須為 CREATED、STOPPED 或 FAILED，目前為 {project.status}"
            )

        # 如果是 STOPPED 或 FAILED 狀態，先清理舊容器
        if project.status in [ProjectStatus.STOPPED, ProjectStatus.FAILED] and project.container_id:
            logger.info(f"清理舊容器: {project.container_id}")
            try:
                container_service.remove_container(project.container_id, force=True)
                logger.info(f"已刪除舊容器: {project.container_id}")
            except Exception as e:
                logger.warning(f"清理舊容器失敗 (將繼續): {e}")

        container_id = None
        try:
            # 更新狀態為 PROVISIONING
            await self._update_project_status(
                project_id, ProjectStatus.PROVISIONING, last_error=None
            )

            # 建立主機目錄結構
            self._prepare_project_directories(project_id)

            # 建立容器
            logger.info(f"建立容器: 專案 {project_id}")
            container = container_service.create_container(
                project_id
            )
            container_id = container["id"]

            # 啟動容器
            container_service.start_container(container_id)

            # 根據專案類型處理
            if project.project_type == ProjectType.SANDBOX:
                # SANDBOX 類型：建立初始工作空間（不需要 clone repo）
                logger.info(f"設置 SANDBOX 工作空間: 專案 {project_id}")
                self._setup_sandbox_workspace(project_id)
            else:
                # REFACTOR 類型：Clone repository
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

    def _prepare_project_directories(self, project_id: str) -> None:
        """準備專案目錄結構"""
        import os
        import shutil
        from ..config import settings
        
        project_dir = f"{settings.docker_volume_prefix}/{project_id}"
        
        # 清理舊的 repo 目錄（如果存在）
        repo_dir = f"{project_dir}/repo"
        if os.path.exists(repo_dir):
            logger.info(f"清理舊的 repo 目錄: {repo_dir}")
            shutil.rmtree(repo_dir)
        
        os.makedirs(f"{project_dir}/repo", exist_ok=True)
        os.makedirs(f"{project_dir}/artifacts", exist_ok=True)
        logger.info(f"建立專案目錄: {project_dir}")

    def _setup_sandbox_workspace(self, project_id: str) -> None:
        """設置 SANDBOX 工作空間（建立初始檔案結構）"""
        import os
        from ..config import settings
        
        project_dir = f"{settings.docker_volume_prefix}/{project_id}"
        
        # 建立 memory 目錄
        memory_dir = f"{project_dir}/memory"
        os.makedirs(memory_dir, exist_ok=True)
        
        # 建立初始 AGENTS.md
        agents_md_path = f"{memory_dir}/AGENTS.md"
        if not os.path.exists(agents_md_path):
            with open(agents_md_path, "w", encoding="utf-8") as f:
                f.write("""# Agent Memory

這是你的工作空間。你可以在這裡自由探索和創建檔案。

## 可用工具

- `ls` - 列出目錄內容
- `read_file` - 讀取檔案
- `write_file` - 寫入檔案
- `edit_file` - 編輯檔案
- `glob` - 搜尋檔案
- `grep` - 搜尋檔案內容

## 工作目錄

- `/workspace/repo/` - 主要工作目錄
- `/workspace/memory/` - 記憶和筆記
- `/workspace/artifacts/` - 產出檔案
""")
            logger.info(f"建立初始 AGENTS.md: {agents_md_path}")

    async def _update_project_status(
        self,
        project_id: str,
        status: ProjectStatus,
        container_id: str = None,
        last_error: str = None,
    ) -> None:
        """更新專案狀態"""
        obj_id = validate_and_convert_object_id(project_id, "project_id")
        if not obj_id:
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

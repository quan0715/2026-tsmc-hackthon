"""邊界條件測試 - 分散在各服務層"""
import pytest
from app.services.project_service import ProjectService
from app.services.auth_service import AuthService
from app.services.container_service import ContainerService
from app.services.agent_run_service import AgentRunService
from unittest.mock import MagicMock
import asyncio


class TestProjectServiceEdgeCases:
    """Project Service 邊界條件"""

    @pytest.mark.asyncio
    async def test_create_project_with_long_title(self, project_service: ProjectService, test_user):
        """測試超長標題"""
        long_title = "A" * 500  # 500 字元標題

        from app.schemas.project import CreateProjectRequest
        request = CreateProjectRequest(
            title=long_title,
            repo_url="https://github.com/test/repo.git",
            branch="main",
            spec="Test"
        )

        project = await project_service.create_project(
            request,
            owner_id=test_user.id,
            owner_email=test_user.email
        )

        # 應該成功建立（或被截斷）
        assert project is not None
        assert len(project.title) <= 500

    @pytest.mark.asyncio
    async def test_create_project_with_special_characters(
        self,
        project_service: ProjectService,
        test_user
    ):
        """測試特殊字元"""
        from app.schemas.project import CreateProjectRequest
        request = CreateProjectRequest(
            title="Test <script>alert('xss')</script>",
            repo_url="https://github.com/test/repo.git",
            branch="main",
            spec="Test with 中文 and émojis 🚀"
        )

        project = await project_service.create_project(
            request,
            owner_id=test_user.id,
            owner_email=test_user.email
        )

        assert project is not None
        assert project.title is not None

    @pytest.mark.asyncio
    async def test_list_projects_pagination_edge_cases(
        self,
        project_service: ProjectService,
        test_user
    ):
        """測試分頁邊界"""
        from app.schemas.project import CreateProjectRequest

        # 建立 5 個專案
        for i in range(5):
            request = CreateProjectRequest(
                repo_url=f"https://github.com/test/repo{i}.git",
                branch="main",
                spec=f"Project {i}"
            )
            await project_service.create_project(
                request,
                owner_id=test_user.id,
                owner_email=test_user.email
            )

        # 測試 skip=0, limit=0
        projects, total = await project_service.list_projects(
            owner_id=test_user.id,
            skip=0,
            limit=0
        )
        assert len(projects) == 0
        assert total == 5

        # 測試 skip=10 (超過總數)
        projects, total = await project_service.list_projects(
            owner_id=test_user.id,
            skip=10,
            limit=10
        )
        assert len(projects) == 0
        assert total == 5

        # 測試 limit=1000 (超大值)
        projects, total = await project_service.list_projects(
            owner_id=test_user.id,
            skip=0,
            limit=1000
        )
        assert len(projects) == 5
        assert total == 5

    @pytest.mark.asyncio
    async def test_concurrent_project_creation(
        self,
        project_service: ProjectService,
        test_user
    ):
        """測試並發建立專案"""
        from app.schemas.project import CreateProjectRequest

        async def create_project(index):
            request = CreateProjectRequest(
                repo_url=f"https://github.com/test/concurrent{index}.git",
                branch="main",
                spec=f"Concurrent {index}"
            )
            return await project_service.create_project(
                request,
                owner_id=test_user.id,
                owner_email=test_user.email
            )

        # 並發建立 10 個專案
        projects = await asyncio.gather(*[create_project(i) for i in range(10)])

        # 確保所有專案都成功建立
        assert len(projects) == 10
        assert all(p is not None for p in projects)

        # 確保所有專案 ID 都是唯一的
        project_ids = [p.id for p in projects]
        assert len(set(project_ids)) == 10


class TestAgentRunServiceEdgeCases:
    """Agent Run Service 邊界條件"""

    @pytest.mark.asyncio
    async def test_mark_failed_concurrent(self, db):
        """測試並發標記失敗"""
        service = AgentRunService(db)

        # 建立 agent run
        run = await service.create_agent_run(
            project_id="test-project",
            iteration_index=0,
            phase="plan"
        )

        # 並發標記失敗
        async def mark_failed(msg):
            await service.mark_failed(run.id, msg)

        await asyncio.gather(
            mark_failed("Error 1"),
            mark_failed("Error 2"),
            mark_failed("Error 3")
        )

        # 驗證最終狀態
        updated_run = await service.get_agent_run_by_id(run.id)
        assert updated_run.status == "FAILED"
        # 錯誤訊息可能是三個之一
        assert updated_run.error_message in ["Error 1", "Error 2", "Error 3"]

    @pytest.mark.asyncio
    async def test_create_agent_run_max_iteration(self, db):
        """測試最大迭代次數"""
        service = AgentRunService(db)

        # 建立多個迭代
        runs = []
        for i in range(100):
            run = await service.create_agent_run(
                project_id="test-project",
                iteration_index=i,
                phase="plan"
            )
            runs.append(run)

        # 確保所有 runs 都建立成功
        assert len(runs) == 100

    @pytest.mark.asyncio
    async def test_get_agent_runs_large_dataset(self, db):
        """測試大量資料分頁"""
        service = AgentRunService(db)

        # 建立 50 個 runs
        for i in range(50):
            await service.create_agent_run(
                project_id="test-large-dataset",
                iteration_index=i,
                phase="plan"
            )

        # 測試分頁
        runs = await service.get_agent_runs(
            project_id="test-large-dataset",
            limit=10
        )
        assert len(runs) == 10

        runs_all = await service.get_agent_runs(
            project_id="test-large-dataset",
            limit=100
        )
        assert len(runs_all) == 50


class TestContainerServiceEdgeCases:
    """Container Service 邊界條件（需要 mock）"""

    @pytest.mark.asyncio
    async def test_exec_command_timeout(self, mock_subprocess, mock_makedirs):
        """測試指令超時"""
        import subprocess

        # Mock timeout
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd=["docker", "exec"],
            timeout=30
        )

        service = ContainerService()

        with pytest.raises(subprocess.TimeoutExpired):
            service.exec_command("test-container", "sleep 100")

    @pytest.mark.asyncio
    async def test_clone_repository_large_repo(self, mock_subprocess, mock_makedirs):
        """測試大型 repo 超時"""
        import subprocess

        # Mock timeout for git clone
        def mock_run_side_effect(*args, **kwargs):
            if "clone" in args[0]:
                raise subprocess.TimeoutExpired(cmd=args[0], timeout=300)
            return MagicMock(returncode=0, stdout="OK\n")

        mock_subprocess.side_effect = mock_run_side_effect

        service = ContainerService()

        with pytest.raises(subprocess.TimeoutExpired):
            service.clone_repository(
                "test-container",
                "https://github.com/large/repo.git",
                "main"
            )

    @pytest.mark.asyncio
    async def test_container_resource_limits(self, mock_subprocess, mock_makedirs):
        """測試資源限制驗證"""
        from app.config import settings

        # Mock成功建立
        mock_subprocess.return_value = MagicMock(
            returncode=0,
            stdout="container123\n"
        )

        service = ContainerService()
        result = service.create_container("test-project")

        # 驗證建立指令包含資源限制
        call_args = mock_subprocess.call_args[0][0]
        assert "--memory" in call_args
        assert "--cpus" in call_args


class TestAuthServiceEdgeCases:
    """Auth Service 邊界條件"""

    @pytest.mark.asyncio
    async def test_create_user_with_very_long_password(self, auth_service: AuthService):
        """測試超長密碼"""
        long_password = "A" * 1000

        user = await auth_service.create_user(
            email="longpass@example.com",
            username="longpass",
            password=long_password
        )

        # 應該成功建立並加密
        assert user is not None
        assert user.password_hash != long_password
        # 驗證密碼應該成功
        assert auth_service.verify_password(long_password, user.password_hash)

    @pytest.mark.asyncio
    async def test_token_with_special_characters_in_email(self, auth_service: AuthService):
        """測試包含特殊字元的 email"""
        user = await auth_service.create_user(
            email="user+test@example.com",
            username="specialuser",
            password="password123"
        )

        token, _ = auth_service.create_access_token(user.id, user.email)

        # 解碼應該成功
        payload = auth_service.decode_token(token)
        assert payload["email"] == "user+test@example.com"

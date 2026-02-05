"""File Operations API 測試 - 需要 mock container_service"""
import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock


@pytest.fixture
async def provisioned_project(auth_client: AsyncClient, test_user):
    """建立一個已 provision 的專案（有 container_id）"""
    # 建立專案
    response = await auth_client.post(
        "/api/v1/projects",
        json={
            "repo_url": "https://github.com/test/repo.git",
            "branch": "main",
            "spec": "Test project"
        }
    )
    project_id = response.json()["id"]

    # 手動更新專案，加入 container_id
    from app.database.mongodb import get_database_client
    from bson import ObjectId
    from app.models.project import ProjectStatus

    client = get_database_client()
    db = client["refactor_agent_test"]
    await db.projects.update_one(
        {"_id": ObjectId(project_id)},
        {
            "$set": {
                "container_id": "test-container-123",
                "status": ProjectStatus.READY
            }
        }
    )

    return project_id


@pytest.fixture
def mock_container_service_list_files(monkeypatch):
    """Mock ContainerService.list_files"""
    def mock_init(self):
        pass

    def mock_list_files(self, container_id, path="/workspace", exclude_patterns=None):
        return {
            "type": "directory",
            "name": "workspace",
            "path": "/workspace",
            "children": [
                {
                    "type": "directory",
                    "name": "repo",
                    "path": "/workspace/repo",
                    "children": [
                        {"type": "file", "name": "main.py", "path": "/workspace/repo/main.py"},
                        {"type": "file", "name": "README.md", "path": "/workspace/repo/README.md"}
                    ]
                },
                {
                    "type": "directory",
                    "name": "artifacts",
                    "path": "/workspace/artifacts",
                    "children": []
                }
            ]
        }

    from app.services.container_service import ContainerService
    monkeypatch.setattr(ContainerService, "__init__", mock_init)
    monkeypatch.setattr(ContainerService, "list_files", mock_list_files)


@pytest.fixture
def mock_container_service_read_file(monkeypatch):
    """Mock ContainerService.read_file"""
    def mock_init(self):
        pass

    def mock_read_file(self, container_id, file_path):
        if "nonexistent" in file_path:
            raise FileNotFoundError(f"File not found: {file_path}")
        if "large" in file_path:
            raise ValueError("File too large")
        if "agent" in file_path:
            raise ValueError("Access denied")

        return {
            "file_path": file_path,
            "content": "print('Hello World')\n",
            "size": 100,
            "encoding": "utf-8"
        }

    from app.services.container_service import ContainerService
    monkeypatch.setattr(ContainerService, "__init__", mock_init)
    monkeypatch.setattr(ContainerService, "read_file", mock_read_file)


class TestGetFileTree:
    """取得檔案樹測試"""

    @pytest.mark.asyncio
    async def test_get_file_tree_success(
        self,
        auth_client: AsyncClient,
        provisioned_project,
        mock_container_service_list_files
    ):
        """測試取得檔案樹"""
        response = await auth_client.get(
            f"/api/v1/projects/{provisioned_project}/files"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["root"] == "/workspace"
        assert "tree" in data
        assert data["tree"]["type"] == "directory"
        assert len(data["tree"]["children"]) >= 2

    @pytest.mark.asyncio
    async def test_get_file_tree_empty(
        self,
        auth_client: AsyncClient,
        provisioned_project,
        monkeypatch
    ):
        """測試空目錄"""
        def mock_init(self):
            pass

        def mock_list_files(self, container_id, path="/workspace", exclude_patterns=None):
            return {
                "type": "directory",
                "name": "workspace",
                "path": "/workspace",
                "children": []
            }

        from app.services.container_service import ContainerService
        monkeypatch.setattr(ContainerService, "__init__", mock_init)
        monkeypatch.setattr(ContainerService, "list_files", mock_list_files)

        response = await auth_client.get(
            f"/api/v1/projects/{provisioned_project}/files"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tree"]["children"] == []

    @pytest.mark.asyncio
    async def test_get_file_tree_unauthorized(
        self,
        client: AsyncClient,
        provisioned_project,
        auth_service
    ):
        """測試無權訪問"""
        # 建立另一個用戶
        user2 = await auth_service.create_user(
            email="user2@example.com",
            username="user2",
            password="password123"
        )
        token2, _ = auth_service.create_access_token(user2.id, user2.email)

        client.headers["Authorization"] = f"Bearer {token2}"
        response = await client.get(f"/api/v1/projects/{provisioned_project}/files")

        assert response.status_code == 403


class TestReadFileContent:
    """讀取檔案內容測試"""

    @pytest.mark.asyncio
    async def test_read_file_success(
        self,
        auth_client: AsyncClient,
        provisioned_project,
        mock_container_service_read_file
    ):
        """測試讀取檔案內容"""
        response = await auth_client.get(
            f"/api/v1/projects/{provisioned_project}/files/repo/main.py"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["file_path"] == "repo/main.py"
        assert "content" in data
        assert "print('Hello World')" in data["content"]

    @pytest.mark.asyncio
    async def test_read_file_not_found(
        self,
        auth_client: AsyncClient,
        provisioned_project,
        mock_container_service_read_file
    ):
        """測試檔案不存在"""
        response = await auth_client.get(
            f"/api/v1/projects/{provisioned_project}/files/repo/nonexistent.py"
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_read_file_path_traversal_attack(
        self,
        auth_client: AsyncClient,
        provisioned_project,
        mock_container_service_read_file
    ):
        """測試路徑遍歷攻擊防護"""
        response = await auth_client.get(
            f"/api/v1/projects/{provisioned_project}/files/agent/secret.py"
        )

        # 應該被拒絕
        assert response.status_code == 403
        assert "不允許存取 agent 目錄" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_read_file_too_large(
        self,
        auth_client: AsyncClient,
        provisioned_project,
        mock_container_service_read_file
    ):
        """測試檔案過大錯誤"""
        response = await auth_client.get(
            f"/api/v1/projects/{provisioned_project}/files/repo/large-file.bin"
        )

        assert response.status_code == 400


class TestProjectWithoutContainer:
    """未 provision 專案測試"""

    @pytest.mark.asyncio
    async def test_file_tree_without_provision(
        self,
        auth_client: AsyncClient,
        test_user
    ):
        """測試未 provision 專案無法取得檔案樹"""
        # 建立未 provision 專案
        response = await auth_client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "spec": "Test"
            }
        )
        project_id = response.json()["id"]

        # 嘗試取得檔案樹
        response = await auth_client.get(f"/api/v1/projects/{project_id}/files")

        assert response.status_code == 400
        assert "provision" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_read_file_without_provision(
        self,
        auth_client: AsyncClient,
        test_user
    ):
        """測試未 provision 專案無法讀取檔案"""
        # 建立未 provision 專案
        response = await auth_client.post(
            "/api/v1/projects",
            json={
                "repo_url": "https://github.com/test/repo.git",
                "branch": "main",
                "spec": "Test"
            }
        )
        project_id = response.json()["id"]

        # 嘗試讀取檔案
        response = await auth_client.get(
            f"/api/v1/projects/{project_id}/files/main.py"
        )

        assert response.status_code == 400
        assert "provision" in response.json()["detail"].lower()

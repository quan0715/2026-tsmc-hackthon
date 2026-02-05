"""Container Service 單元測試 - 需要 mock subprocess"""
import pytest
import subprocess
from unittest.mock import MagicMock, patch
from app.services.container_service import ContainerService


class MockCompletedProcess:
    """Mock subprocess.CompletedProcess"""
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


@pytest.fixture
def mock_subprocess(monkeypatch):
    """Mock subprocess.run"""
    mock_run = MagicMock()
    monkeypatch.setattr("subprocess.run", mock_run)
    return mock_run


@pytest.fixture
def mock_makedirs(monkeypatch):
    """Mock os.makedirs"""
    mock_makedirs = MagicMock()
    monkeypatch.setattr("os.makedirs", mock_makedirs)
    return mock_makedirs


@pytest.fixture
def container_service(mock_subprocess, mock_makedirs):
    """ContainerService fixture with mocked subprocess"""
    # Mock Docker version check (called in __init__)
    mock_subprocess.return_value = MockCompletedProcess(
        returncode=0,
        stdout="20.10.17\n"
    )
    return ContainerService()


class TestCreateContainer:
    """建立容器測試"""

    @pytest.mark.asyncio
    async def test_create_container_success(self, container_service, mock_subprocess, mock_makedirs):
        """測試成功建立容器"""
        # Setup mock
        mock_subprocess.return_value = MockCompletedProcess(
            returncode=0,
            stdout="abc123containerid\n"
        )

        # Execute
        result = container_service.create_container(project_id="test-project-1")

        # Assertions
        assert result["id"] == "abc123containerid"
        # 確認有建立目錄
        assert mock_makedirs.call_count >= 2  # repo and artifacts
        # 確認 docker create 被呼叫
        mock_subprocess.assert_called()

    @pytest.mark.asyncio
    async def test_create_container_failure(self, container_service, mock_subprocess):
        """測試 subprocess 失敗處理"""
        # Setup mock - 模擬 docker create 失敗
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["docker", "create"],
            stderr="Image not found"
        )

        # Execute and assert
        with pytest.raises(Exception, match="建立容器失敗"):
            container_service.create_container(project_id="test-project-1")


class TestStartContainer:
    """啟動容器測試"""

    @pytest.mark.asyncio
    async def test_start_container_success(self, container_service, mock_subprocess):
        """測試啟動容器"""
        # Setup mock
        mock_subprocess.return_value = MockCompletedProcess(
            returncode=0,
            stdout="ready\n"
        )

        # Execute
        container_service.start_container("test-container", wait_ready=False)

        # Assert docker start was called
        calls = mock_subprocess.call_args_list
        assert any("start" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_start_container_not_found(self, container_service, mock_subprocess):
        """測試容器不存在"""
        # Setup mock
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["docker", "start"],
            stderr="No such container"
        )

        # Execute and assert
        with pytest.raises(Exception, match="啟動容器失敗"):
            container_service.start_container("nonexistent-container", wait_ready=False)


class TestStopContainer:
    """停止容器測試"""

    @pytest.mark.asyncio
    async def test_stop_container_success(self, container_service, mock_subprocess):
        """測試停止容器"""
        # Setup mock
        mock_subprocess.return_value = MockCompletedProcess(returncode=0)

        # Execute
        container_service.stop_container("test-container")

        # Assert docker stop was called
        calls = mock_subprocess.call_args_list
        assert any("stop" in str(call) for call in calls)


class TestRemoveContainer:
    """刪除容器測試"""

    @pytest.mark.asyncio
    async def test_remove_container_success(self, container_service, mock_subprocess):
        """測試刪除容器"""
        # Setup mock
        mock_subprocess.return_value = MockCompletedProcess(returncode=0)

        # Execute
        container_service.remove_container("test-container")

        # Assert docker rm was called
        calls = mock_subprocess.call_args_list
        assert any("rm" in str(call) for call in calls)


class TestGetContainerStatus:
    """查詢容器狀態測試"""

    @pytest.mark.asyncio
    async def test_get_container_status_running(self, container_service, mock_subprocess):
        """測試查詢運行中狀態"""
        # Setup mock
        mock_subprocess.return_value = MockCompletedProcess(
            returncode=0,
            stdout='[{"State": {"Status": "running"}}]\n'
        )

        # Execute
        status = container_service.get_container_status("test-container")

        # Assert
        assert status["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_container_status_stopped(self, container_service, mock_subprocess):
        """測試查詢停止狀態"""
        # Setup mock
        mock_subprocess.return_value = MockCompletedProcess(
            returncode=0,
            stdout='[{"State": {"Status": "exited"}}]\n'
        )

        # Execute
        status = container_service.get_container_status("test-container")

        # Assert
        assert status["status"] == "exited"


class TestCloneRepository:
    """Git clone 測試"""

    @pytest.mark.asyncio
    async def test_clone_repository_success(self, container_service, mock_subprocess):
        """測試 git clone 成功"""
        # Setup mock
        mock_subprocess.return_value = MockCompletedProcess(
            returncode=0,
            stdout="Cloning into 'repo'...\n"
        )

        # Execute
        container_service.clone_repository(
            container_id="test-container",
            repo_url="https://github.com/test/repo.git",
            branch="main"
        )

        # Assert git clone was called
        calls = mock_subprocess.call_args_list
        assert any("clone" in str(call) for call in calls)

    @pytest.mark.asyncio
    async def test_clone_repository_invalid_url(self, container_service, mock_subprocess):
        """測試無效 repo URL"""
        # Setup mock - 模擬 git clone 失敗
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=128,
            cmd=["git", "clone"],
            stderr="fatal: repository not found"
        )

        # Execute and assert
        with pytest.raises(Exception):
            container_service.clone_repository(
                container_id="test-container",
                repo_url="https://github.com/invalid/repo.git",
                branch="main"
            )

    @pytest.mark.asyncio
    async def test_clone_repository_timeout(self, container_service, mock_subprocess):
        """測試 clone 超時"""
        # Setup mock - 模擬超時
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd=["git", "clone"],
            timeout=300
        )

        # Execute and assert
        with pytest.raises(subprocess.TimeoutExpired):
            container_service.clone_repository(
                container_id="test-container",
                repo_url="https://github.com/large/repo.git",
                branch="main"
            )


class TestExecCommand:
    """執行指令測試"""

    @pytest.mark.asyncio
    async def test_exec_command_success(self, container_service, mock_subprocess):
        """測試執行指令成功"""
        # Setup mock
        mock_subprocess.return_value = MockCompletedProcess(
            returncode=0,
            stdout="Hello World\n"
        )

        # Execute
        result = container_service.exec_command(
            container_id="test-container",
            command="echo 'Hello World'"
        )

        # Assert
        assert result["exit_code"] == 0
        assert "Hello World" in result["output"]

    @pytest.mark.asyncio
    async def test_exec_command_failure(self, container_service, mock_subprocess):
        """測試指令執行失敗"""
        # Setup mock
        mock_subprocess.return_value = MockCompletedProcess(
            returncode=1,
            stderr="command not found\n"
        )

        # Execute
        result = container_service.exec_command(
            container_id="test-container",
            command="nonexistent-command"
        )

        # Assert
        assert result["exit_code"] == 1
        assert "command not found" in result.get("error", "")


class TestListFiles:
    """列出檔案測試"""

    @pytest.mark.asyncio
    async def test_list_files_success(self, container_service, mock_subprocess):
        """測試列出檔案"""
        # Setup mock
        mock_subprocess.return_value = MockCompletedProcess(
            returncode=0,
            stdout="file1.py\nfile2.py\nREADME.md\n"
        )

        # Execute
        files = container_service.list_files(
            container_id="test-container",
            path="/workspace/repo"
        )

        # Assert
        assert len(files) == 3
        assert "file1.py" in files


class TestReadFile:
    """讀取檔案測試"""

    @pytest.mark.asyncio
    async def test_read_file_success(self, container_service, mock_subprocess):
        """測試讀取檔案"""
        # Setup mock
        mock_subprocess.return_value = MockCompletedProcess(
            returncode=0,
            stdout="print('Hello World')\n"
        )

        # Execute
        content = container_service.read_file(
            container_id="test-container",
            file_path="/workspace/repo/test.py"
        )

        # Assert
        assert "Hello World" in content

    @pytest.mark.asyncio
    async def test_read_file_not_found(self, container_service, mock_subprocess):
        """測試檔案不存在"""
        # Setup mock
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=["cat"],
            stderr="No such file or directory"
        )

        # Execute and assert
        with pytest.raises(Exception):
            container_service.read_file(
                container_id="test-container",
                file_path="/workspace/repo/nonexistent.py"
            )

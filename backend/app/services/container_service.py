"""容器服務層"""
import subprocess
import json
from typing import Optional, Dict, Any
import logging

from ..config import settings

logger = logging.getLogger(__name__)


class ContainerService:
    """Docker 容器服務 (使用subprocess調用docker命令)"""

    def __init__(self):
        try:
            # 測試 Docker 是否可用
            result = subprocess.run(
                ["docker", "version", "--format", "{{.Server.Version}}"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"成功連接到 Docker: {result.stdout.strip()}")
        except subprocess.CalledProcessError as e:
            logger.error(f"無法連接到 Docker: {e}")
            raise
        except FileNotFoundError:
            logger.error("Docker 命令不存在")
            raise

    def create_container(
        self,
        project_id: str,
        image: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """建立容器"""
        if image is None:
            image = settings.docker_base_image

        try:
            # 建立容器
            cmd = [
                "docker", "create",
                "--name", f"refactor-project-{project_id}",
                "--network", settings.docker_network,
                "-t",  # tty
                "-i",  # stdin_open
                "--memory", settings.container_memory_limit,
                "--cpus", str(settings.container_cpu_limit),
                "-v", f"{settings.docker_volume_prefix}/{project_id}:/workspace",
                image
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            container_id = result.stdout.strip()
            logger.info(f"建立容器: {container_id}")
            return {"id": container_id}
        except subprocess.CalledProcessError as e:
            logger.error(f"建立容器失敗: {e.stderr}")
            raise Exception(f"建立容器失敗: {e.stderr}")

    def start_container(self, container_id: str) -> None:
        """啟動容器"""
        try:
            subprocess.run(
                ["docker", "start", container_id],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"啟動容器: {container_id}")
        except subprocess.CalledProcessError as e:
            logger.error(f"啟動容器失敗: {e.stderr}")
            raise Exception(f"啟動容器失敗: {e.stderr}")

    def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """停止容器"""
        try:
            subprocess.run(
                ["docker", "stop", "-t", str(timeout), container_id],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"停止容器: {container_id}")
        except subprocess.CalledProcessError as e:
            if "No such container" in e.stderr:
                logger.warning(f"容器不存在: {container_id}")
            else:
                logger.error(f"停止容器失敗: {e.stderr}")
                raise Exception(f"停止容器失敗: {e.stderr}")

    def remove_container(self, container_id: str, force: bool = False) -> None:
        """刪除容器"""
        try:
            cmd = ["docker", "rm", container_id]
            if force:
                cmd.insert(2, "-f")

            subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"刪除容器: {container_id}")
        except subprocess.CalledProcessError as e:
            if "No such container" in e.stderr:
                logger.warning(f"容器不存在: {container_id}")
            else:
                logger.error(f"刪除容器失敗: {e.stderr}")
                raise Exception(f"刪除容器失敗: {e.stderr}")

    def get_container_status(self, container_id: str) -> Optional[Dict[str, Any]]:
        """獲取容器狀態"""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_id],
                capture_output=True,
                text=True,
                check=True
            )

            info = json.loads(result.stdout)[0]
            return {
                "id": info["Id"][:12],
                "name": info["Name"].lstrip("/"),
                "status": info["State"]["Status"],
                "image": info["Config"]["Image"],
            }
        except subprocess.CalledProcessError:
            return None
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.error(f"解析容器資訊失敗: {e}")
            return None

    def get_container_info(self, container_id: str) -> Optional[Dict[str, Any]]:
        """獲取容器詳細資訊"""
        try:
            result = subprocess.run(
                ["docker", "inspect", container_id],
                capture_output=True,
                text=True,
                check=True
            )

            info = json.loads(result.stdout)[0]
            return {
                "id": info["Id"][:12],
                "name": info["Name"].lstrip("/"),
                "status": info["State"]["Status"],
                "image": info["Config"]["Image"],
                "created": info["Created"],
                "state": info["State"],
            }
        except subprocess.CalledProcessError:
            return None
        except (json.JSONDecodeError, IndexError, KeyError) as e:
            logger.error(f"解析容器資訊失敗: {e}")
            return None

    def clone_repository(
        self,
        container_id: str,
        repo_url: str,
        branch: str = "main",
        target_dir: str = "/workspace/repo",
    ) -> Dict[str, Any]:
        """在容器中 clone repository"""
        try:
            # 執行 git clone 指令
            clone_cmd = f"git clone --branch {branch} --depth {settings.git_depth} {repo_url} {target_dir}"

            result = subprocess.run(
                ["docker", "exec", "-w", "/workspace", container_id, "sh", "-c", clone_cmd],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                error_msg = result.stderr or result.stdout
                logger.error(f"Clone repository 失敗: {error_msg}")
                raise Exception(f"Clone repository 失敗: {error_msg}")

            logger.info(f"成功 clone repository: {repo_url}")
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            logger.error(f"Clone repository 失敗: {e}")
            raise

    def exec_command(
        self,
        container_id: str,
        command: str,
        workdir: str = "/workspace/repo",
    ) -> Dict[str, Any]:
        """在容器中執行指令"""
        try:
            result = subprocess.run(
                ["docker", "exec", "-w", workdir, container_id, "sh", "-c", command],
                capture_output=True,
                text=True
            )

            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except Exception as e:
            logger.error(f"執行指令失敗: {e}")
            raise

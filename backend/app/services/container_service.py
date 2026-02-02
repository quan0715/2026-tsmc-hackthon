"""容器服務層"""
import subprocess
import json
import os
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
        """建立容器（Agent 程式碼已烤進 base image）"""
        if image is None:
            image = settings.docker_base_image

        try:
            # 準備環境變數
            env_vars = []
            # 傳遞 ANTHROPIC_API_KEY（如果有設定）
            if hasattr(settings, 'anthropic_api_key') and settings.anthropic_api_key:
                env_vars.extend(["-e", f"ANTHROPIC_API_KEY={settings.anthropic_api_key}"])

            # 建立容器
            # 分別掛載 repo 和 artifacts，保留 image 中的 agent 目錄
            cmd = [
                "docker", "create",
                "--name", f"refactor-project-{project_id}",
                "--network", settings.docker_network,
                "-t",  # tty
                "-i",  # stdin_open
                "--memory", settings.container_memory_limit,
                "--cpus", str(settings.container_cpu_limit),
                *env_vars,  # 加入環境變數
                image
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            container_id = result.stdout.strip()
            logger.info(f"建立容器: {container_id} (Agent 已內建於 image)")
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

    def exec_command_with_env(
        self,
        container_id: str,
        command: str,
        env_vars: Dict[str, str],
        workdir: str = "/workspace"
    ) -> Dict[str, Any]:
        """在容器中執行指令（帶環境變數）"""
        try:
            cmd = ["docker", "exec"]

            # 添加環境變數
            for key, value in env_vars.items():
                cmd.extend(["-e", f"{key}={value}"])

            cmd.extend(["-w", workdir, container_id, "sh", "-c", command])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  # 10 分鐘超時
            )

            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            logger.error(f"執行超時 (10 分鐘)")
            raise Exception("執行超時")
        except Exception as e:
            logger.error(f"執行指令失敗: {e}")
            raise

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
        """建立容器

        Args:
            project_id: 專案 ID
            image: Docker 映像名稱
        """
        if image is None:
            image = settings.docker_base_image

        try:
            # 準備專案工作區目錄
            project_dir = f"{settings.docker_volume_prefix}/{project_id}"
            os.makedirs(f"{project_dir}/repo", exist_ok=True)
            os.makedirs(f"{project_dir}/artifacts", exist_ok=True)

            # 準備 volume mounts
            volume_args = [
                "-v", f"{project_dir}/repo:/workspace/repo",
                "-v", f"{project_dir}/artifacts:/workspace/artifacts"
            ]

            # 準備環境變數
            env_vars = []

            # 傳遞 ANTHROPIC_API_KEY（如果有設定）
            if hasattr(settings, 'anthropic_api_key') and settings.anthropic_api_key:
                env_vars.extend(["-e", f"ANTHROPIC_API_KEY={settings.anthropic_api_key}"])

            # 傳遞 POSTGRES_URL（用於 LangGraph 持久化 - 必填）
            if not settings.postgres_url:
                raise Exception(
                    "POSTGRES_URL is required but not configured. "
                    "Please set POSTGRES_URL in .env file."
                )
            env_vars.extend(["-e", f"POSTGRES_URL={settings.postgres_url}"])
            logger.info(f"容器將使用 PostgreSQL 持久化: {settings.postgres_url}")

            # 傳遞 GCP Project ID（用於 Vertex AI 模型）
            if settings.gcp_project_id:
                env_vars.extend(["-e", f"GCP_PROJECT_ID={settings.gcp_project_id}"])
                logger.info(f"容器將使用 GCP Project: {settings.gcp_project_id}")

            # 掛載 GCP Service Account credentials
            # GOOGLE_APPLICATION_CREDENTIALS 是 API 容器內路徑（如 /app/gcp-credentials.json）
            # 複製到 DOCKER_VOLUME_PREFIX（宿主機路徑）後掛載給 project 容器
            if settings.google_application_credentials:
                src_path = settings.google_application_credentials
                if os.path.exists(src_path):
                    import shutil
                    host_creds_path = f"{settings.docker_volume_prefix}/gcp-credentials.json"
                    os.makedirs(settings.docker_volume_prefix, exist_ok=True)
                    shutil.copy2(src_path, host_creds_path)
                    container_creds_path = "/workspace/credentials/gcp-credentials.json"
                    volume_args.extend(["-v", f"{host_creds_path}:{container_creds_path}:ro"])
                    env_vars.extend(["-e", f"GOOGLE_APPLICATION_CREDENTIALS={container_creds_path}"])
                    logger.info("容器將掛載 GCP credentials")
                else:
                    logger.warning(f"GCP credentials 檔案不存在: {src_path}")

            # 建立容器
            cmd = [
                "docker", "create",
                "--name", f"refactor-project-{project_id}",
                "--network", settings.docker_network,
                "-t",  # tty
                "-i",  # stdin_open
                "--memory", settings.container_memory_limit,
                "--cpus", str(settings.container_cpu_limit),
                *volume_args,  # 加入 volume 參數
                *env_vars,     # 加入環境變數
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

    def start_container(self, container_id: str, wait_ready: bool = True) -> None:
        """啟動容器"""
        try:
            subprocess.run(
                ["docker", "start", container_id],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"啟動容器: {container_id}")
            
            # 等待容器就緒
            if wait_ready:
                self._wait_container_ready(container_id)
                
        except subprocess.CalledProcessError as e:
            logger.error(f"啟動容器失敗: {e.stderr}")
            raise Exception(f"啟動容器失敗: {e.stderr}")
    
    def _wait_container_ready(self, container_id: str, timeout: int = 30) -> None:
        """等待容器就緒（可執行指令）"""
        import time
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # 嘗試執行簡單指令確認容器就緒
                result = subprocess.run(
                    ["docker", "exec", container_id, "echo", "ready"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0 and "ready" in result.stdout:
                    logger.info(f"容器已就緒: {container_id}")
                    return
            except subprocess.TimeoutExpired:
                pass
            except subprocess.CalledProcessError:
                pass
            
            time.sleep(1)
        
        logger.warning(f"容器就緒超時，繼續嘗試: {container_id}")

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
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """在容器中 clone repository"""
        try:
            # 先清除目標目錄（如果存在）
            logger.info(f"清理目標目錄: {target_dir}")
            cleanup_cmd = f"rm -rf {target_dir}"
            subprocess.run(
                ["docker", "exec", "-w", "/workspace", container_id, "sh", "-c", cleanup_cmd],
                capture_output=True,
                text=True,
                timeout=30
            )

            # 執行 git clone 指令
            clone_cmd = f"git clone --branch {branch} --depth {settings.git_depth} {repo_url} {target_dir} 2>&1"
            logger.info(f"執行 clone 指令: git clone --branch {branch} --depth {settings.git_depth} {repo_url}")

            result = subprocess.run(
                ["docker", "exec", "-w", "/workspace", container_id, "sh", "-c", clone_cmd],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            # 合併 stdout 和 stderr（因為我們用 2>&1 重導向了）
            output = result.stdout + result.stderr
            
            if result.returncode != 0:
                # 過濾掉正常的 git 輸出，提取真正的錯誤訊息
                error_lines = []
                for line in output.split('\n'):
                    line = line.strip()
                    # 跳過正常的狀態訊息
                    if line and not line.startswith('Cloning into'):
                        error_lines.append(line)
                
                error_msg = '\n'.join(error_lines) if error_lines else output
                logger.error(f"Clone repository 失敗 (exit code: {result.returncode}): {error_msg}")
                raise Exception(f"Clone repository 失敗: {error_msg}")

            logger.info(f"成功 clone repository: {repo_url}")
            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            error_msg = f"Clone repository 超時 ({timeout}秒)"
            logger.error(error_msg)
            raise Exception(error_msg)
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

    def list_files(
        self,
        container_id: str,
        path: str = "/workspace",
        exclude_patterns: list = None
    ) -> list:
        """列出容器中的檔案樹
        
        Args:
            container_id: 容器 ID
            path: 要列出的根目錄
            exclude_patterns: 要排除的路徑模式列表
        
        Returns:
            檔案樹結構列表
        """
        if exclude_patterns is None:
            exclude_patterns = ["/workspace/agent"]
        
        try:
            # 使用 find 指令列出所有檔案和目錄
            # 輸出格式: type|path (d=目錄, f=檔案)
            exclude_args = " ".join([f"! -path '{p}' ! -path '{p}/*'" for p in exclude_patterns])
            cmd = f"find {path} -mindepth 1 {exclude_args} -printf '%y|%p\\n' 2>/dev/null | sort"
            
            result = subprocess.run(
                ["docker", "exec", container_id, "sh", "-c", cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.warning(f"列出檔案失敗: {result.stderr}")
                return []
            
            # 解析輸出並建構樹狀結構
            lines = result.stdout.strip().split('\n') if result.stdout.strip() else []
            return self._build_file_tree(lines, path)
            
        except subprocess.TimeoutExpired:
            logger.error("列出檔案超時")
            return []
        except Exception as e:
            logger.error(f"列出檔案失敗: {e}")
            return []

    def _build_file_tree(self, lines: list, root_path: str) -> list:
        """將扁平的檔案列表轉換為樹狀結構"""
        # 建立路徑到節點的映射
        nodes = {}
        root_children = []
        
        for line in lines:
            if not line or '|' not in line:
                continue
            
            file_type, full_path = line.split('|', 1)
            
            # 計算相對路徑
            rel_path = full_path[len(root_path):].lstrip('/')
            if not rel_path:
                continue
            
            name = os.path.basename(full_path)
            node = {
                "name": name,
                "path": rel_path,
                "type": "directory" if file_type == 'd' else "file",
            }
            
            if file_type == 'd':
                node["children"] = []
            
            nodes[rel_path] = node
            
            # 找到父節點
            parent_path = os.path.dirname(rel_path)
            if parent_path and parent_path in nodes:
                nodes[parent_path]["children"].append(node)
            elif not parent_path:
                root_children.append(node)
        
        # 對每個目錄的子節點排序（目錄在前，檔案在後，各自按名稱排序）
        def sort_children(node):
            if "children" in node:
                node["children"].sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"].lower()))
                for child in node["children"]:
                    sort_children(child)
        
        for node in root_children:
            sort_children(node)
        
        root_children.sort(key=lambda x: (0 if x["type"] == "directory" else 1, x["name"].lower()))
        
        return root_children

    def read_file(
        self,
        container_id: str,
        file_path: str,
        max_size: int = 1024 * 1024  # 1MB 限制
    ) -> Dict[str, Any]:
        """讀取容器中的檔案內容
        
        Args:
            container_id: 容器 ID
            file_path: 檔案路徑（相對於 /workspace 或絕對路徑）
            max_size: 最大讀取大小（bytes）
        
        Returns:
            包含 path, content, size 的字典
        """
        # 確保路徑安全
        if '..' in file_path:
            raise ValueError("路徑不能包含 ..")
        
        # 如果不是絕對路徑，加上 /workspace 前綴
        if not file_path.startswith('/'):
            full_path = f"/workspace/{file_path}"
        else:
            full_path = file_path
        
        try:
            # 先檢查檔案大小
            size_cmd = f"stat -c %s '{full_path}' 2>/dev/null || echo 0"
            size_result = subprocess.run(
                ["docker", "exec", container_id, "sh", "-c", size_cmd],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            file_size = int(size_result.stdout.strip() or 0)
            
            if file_size == 0:
                # 檔案不存在或為空
                raise FileNotFoundError(f"檔案不存在或為空: {full_path}")
            
            if file_size > max_size:
                raise ValueError(f"檔案過大: {file_size} bytes (最大 {max_size} bytes)")
            
            # 讀取檔案內容
            read_cmd = f"cat '{full_path}'"
            result = subprocess.run(
                ["docker", "exec", container_id, "sh", "-c", read_cmd],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                raise FileNotFoundError(f"無法讀取檔案: {result.stderr}")
            
            return {
                "path": file_path,
                "content": result.stdout,
                "size": file_size
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"讀取檔案超時: {full_path}")
            raise Exception("讀取檔案超時")
        except (FileNotFoundError, ValueError):
            raise
        except Exception as e:
            logger.error(f"讀取檔案失敗: {e}")
            raise

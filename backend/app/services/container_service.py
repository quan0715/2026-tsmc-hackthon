"""容器服務層"""
import subprocess
import json
import os
import re
import shlex
from typing import Optional, Dict, Any
import logging

from ..config import settings

logger = logging.getLogger(__name__)


def _sanitize_git_url(url: str) -> str:
    """驗證並清理 Git URL
    
    只允許 http(s):// 和 git@ 格式的 URL
    防止命令注入攻擊
    """
    if not url:
        raise ValueError("Git URL 不能為空")
    
    # 放寬一點的通用 URL 格式（允許子路徑）
    # 但確保不含危險字元
    # 支援: https://github.com/user/repo.git, https://github.com/user/repo, git@github.com:user/repo.git
    safe_pattern = r'^(https?://|git@)[a-zA-Z0-9\-_.@:/]+$'
    
    if not re.match(safe_pattern, url):
        raise ValueError(f"無效的 Git URL 格式: {url}")
    
    # 額外檢查：不允許 shell 特殊字元
    dangerous_chars = [';', '&', '|', '$', '`', '(', ')', '{', '}', '[', ']', '<', '>', '!', '\n', '\r']
    for char in dangerous_chars:
        if char in url:
            raise ValueError(f"Git URL 包含不允許的字元: {char}")
    
    return url


def _sanitize_branch_name(branch: str) -> str:
    """驗證並清理 Git branch 名稱
    
    防止命令注入攻擊
    """
    if not branch:
        return "main"
    
    # Git branch 名稱只允許特定字元
    # 參考: https://git-scm.com/docs/git-check-ref-format
    safe_pattern = r'^[a-zA-Z0-9\-_./]+$'
    
    if not re.match(safe_pattern, branch):
        raise ValueError(f"無效的 branch 名稱: {branch}")
    
    # 不允許連續的點或斜線
    if '..' in branch or '//' in branch:
        raise ValueError(f"無效的 branch 名稱: {branch}")
    
    # 不允許以點或斜線開頭或結尾
    if branch.startswith('.') or branch.endswith('.') or branch.startswith('/') or branch.endswith('/'):
        raise ValueError(f"無效的 branch 名稱: {branch}")
    
    return branch


def _sanitize_path(path: str, base_path: str = "/workspace") -> str:
    """驗證並清理檔案路徑
    
    防止路徑遍歷攻擊
    """
    if not path:
        raise ValueError("路徑不能為空")
    
    # 檢查路徑遍歷（包括 URL 編碼的變體）
    path_lower = path.lower()
    # 檢查基本的 .. 和各種編碼形式
    traversal_patterns = [
        '..',           # 基本形式
        '%2e%2e',       # URL 編碼
        '%252e%252e',   # 雙重 URL 編碼
        '%2f',          # URL 編碼的 /
        '%252f',        # 雙重 URL 編碼的 /
    ]
    for pattern in traversal_patterns:
        if pattern in path_lower:
            raise ValueError("路徑不能包含 '..'")
    
    # 不允許 shell 特殊字元
    dangerous_chars = [';', '&', '|', '$', '`', '(', ')', '{', '}', '<', '>', '!', '\n', '\r', "'", '"']
    for char in dangerous_chars:
        if char in path:
            raise ValueError(f"路徑包含不允許的字元: {char}")
    
    # 正規化路徑
    normalized = os.path.normpath(path)
    
    # 如果是相對路徑，加上 base_path
    if not normalized.startswith('/'):
        full_path = os.path.normpath(os.path.join(base_path, normalized))
    else:
        full_path = normalized
    
    # 確保路徑在 base_path 下
    if not full_path.startswith(base_path):
        raise ValueError(f"路徑必須在 {base_path} 下")
    
    return full_path

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

            # 傳遞 POSTGRES_URL（用於 LangGraph 持久化）
            postgres_url = os.environ.get("POSTGRES_URL")
            if postgres_url:
                env_vars.extend(["-e", f"POSTGRES_URL={postgres_url}"])
                logger.info(f"容器將使用 PostgreSQL 持久化")

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
        """在容器中 clone repository
        
        Args:
            container_id: 容器 ID
            repo_url: Git repository URL（會驗證格式）
            branch: Git branch 名稱（會驗證格式）
            target_dir: 目標目錄
            timeout: 超時時間（秒）
        """
        # 驗證並清理輸入參數（防止命令注入）
        safe_repo_url = _sanitize_git_url(repo_url)
        safe_branch = _sanitize_branch_name(branch)
        
        try:
            # 先清除目標目錄（如果存在）
            # 使用 shlex.quote 來安全處理路徑
            logger.info(f"清理目標目錄: {target_dir}")
            cleanup_cmd = f"rm -rf {shlex.quote(target_dir)}"
            subprocess.run(
                ["docker", "exec", "-w", "/workspace", container_id, "sh", "-c", cleanup_cmd],
                capture_output=True,
                text=True,
                timeout=30
            )

            # 執行 git clone 指令
            # 使用 shlex.quote 來安全處理所有參數
            clone_cmd = (
                f"git clone --branch {shlex.quote(safe_branch)} "
                f"--depth {settings.git_depth} "
                f"{shlex.quote(safe_repo_url)} {shlex.quote(target_dir)} 2>&1"
            )
            logger.info(f"執行 clone 指令: git clone --branch {safe_branch} --depth {settings.git_depth} {safe_repo_url}")

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

            logger.info(f"成功 clone repository: {safe_repo_url}")
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
        timeout: int = 300,  # 5 分鐘預設超時
    ) -> Dict[str, Any]:
        """在容器中執行指令
        
        Args:
            container_id: 容器 ID
            command: 要執行的指令
            workdir: 工作目錄
            timeout: 超時時間（秒），預設 5 分鐘
        
        Note:
            指令在隔離的 Docker 容器中執行，安全性由容器隔離保證。
            只有通過認證且擁有專案存取權限的用戶才能執行指令。
        """
        try:
            result = subprocess.run(
                ["docker", "exec", "-w", workdir, container_id, "sh", "-c", command],
                capture_output=True,
                text=True,
                timeout=timeout
            )

            return {
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
            }
        except subprocess.TimeoutExpired:
            logger.error(f"執行超時 ({timeout} 秒): {command[:100]}...")
            raise Exception(f"執行超時 ({timeout} 秒)")
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
        # 驗證並清理路徑（防止路徑遍歷攻擊）
        full_path = _sanitize_path(file_path, "/workspace")
        
        try:
            # 先檢查檔案大小
            # 使用 shlex.quote 來安全處理路徑
            size_cmd = f"stat -c %s {shlex.quote(full_path)} 2>/dev/null || echo 0"
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
            read_cmd = f"cat {shlex.quote(full_path)}"
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

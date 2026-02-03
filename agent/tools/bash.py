"""Bash 工具 - 在 shell 中執行命令

參考: https://platform.claude.com/docs/zh-TW/agents-and-tools/tool-use/bash-tool
"""

import subprocess
import os
from typing import Optional


# 全域 bash 會話狀態（模擬持久會話）
_session_state = {
    "cwd": "/workspace/repo",
    "env": {},
}


def bash(
    command: Optional[str] = None,
    restart: bool = False,
    timeout: int = 120,
) -> str:
    """在持久的 bash 會話中執行 shell 命令。

    此工具提供：
    - 維持狀態的持久 bash 會話
    - 運行任何 shell 命令的能力
    - 訪問環境變數和工作目錄
    - 命令鏈接和腳本編寫功能

    使用案例：
    - 開發工作流程：運行構建命令、測試和開發工具
    - 系統自動化：執行腳本、管理文件、自動化任務
    - 數據處理：處理文件、運行分析腳本
    - 環境設置：安裝軟件包、配置環境

    Args:
        command: 要執行的 bash 命令（除非使用 restart，否則為必需）
        restart: 設置為 True 以重新啟動 bash 會話（重置工作目錄和環境變數）
        timeout: 執行超時時間（秒），預設 120 秒

    Returns:
        str: 命令執行結果，包含 stdout 和 stderr

    Examples:
        # 運行命令
        >>> bash("ls -la *.py")
        "... file listing ..."

        # 檢查環境
        >>> bash("python3 --version")
        "Python 3.11.5"

        # 安裝套件
        >>> bash("pip install requests")
        "Successfully installed requests-2.31.0"

        # 執行 Python 腳本
        >>> bash("python3 main.py")
        "Hello, World!"

        # 重新啟動會話
        >>> bash(restart=True)
        "Bash session restarted. Working directory: /workspace/repo"

    Notes:
        - 會話狀態（工作目錄、環境變數）在命令之間保持
        - 無法處理交互式命令（vim、less、密碼提示等）
        - 大型輸出會被截斷以防止 token 限制問題
    """
    global _session_state

    # 處理重啟請求
    if restart:
        _session_state = {
            "cwd": "/workspace/repo",
            "env": {},
        }
        cwd = _session_state['cwd']
        return f"Bash session restarted. Working directory: {cwd}"

    # 驗證命令
    if not command:
        return "Error: 'command' is required unless using 'restart'"

    # 確保工作目錄存在
    cwd = _session_state["cwd"]
    if not os.path.exists(cwd):
        os.makedirs(cwd, exist_ok=True)

    # 合併環境變數
    env = {**os.environ, **_session_state["env"]}

    try:
        # 使用 bash -c 執行命令，確保使用 bash shell
        result = subprocess.run(
            ["bash", "-c", command],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )

        # 處理輸出
        output = result.stdout
        if result.stderr:
            output += f"\n{result.stderr}"

        # 截斷大型輸出
        output = _truncate_output(output)

        # 如果有退出碼錯誤，附加到輸出
        if result.returncode != 0:
            output = output.rstrip()
            output += f"\n[exit code: {result.returncode}]"

        return output.strip() if output.strip() else "(no output)"

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"
    except FileNotFoundError:
        return "Error: bash: command not found"
    except PermissionError as e:
        return f"Error: Permission denied: {e}"
    except Exception as e:
        return f"Error: {type(e).__name__}: {str(e)}"


def _truncate_output(
    output: str, max_lines: int = 200, max_chars: int = 50000
) -> str:
    """截斷大型輸出以防止 token 限制問題。

    Args:
        output: 原始輸出
        max_lines: 最大行數
        max_chars: 最大字符數

    Returns:
        str: 截斷後的輸出
    """
    # 先檢查字符數
    if len(output) > max_chars:
        output = output[:max_chars]
        output += (
            f"\n\n... Output truncated ({len(output)} characters shown) ..."
        )
        return output

    # 再檢查行數
    lines = output.split('\n')
    if len(lines) > max_lines:
        truncated = '\n'.join(lines[:max_lines])
        truncated += (
            f"\n\n... Output truncated "
            f"({len(lines)} total lines, showing first {max_lines}) ..."
        )
        return truncated

    return output


# 額外的輔助函數，用於更新會話狀態
def _update_cwd_from_command(command: str) -> None:
    """嘗試從 cd 命令更新工作目錄（未來擴展用）"""
    # 這是一個簡化的實現，真正的持久會話需要更複雜的處理
    pass

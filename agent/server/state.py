"""Server State - 全域狀態管理"""

from typing import Dict, TYPE_CHECKING

if TYPE_CHECKING:
    from agent.deep_agent import RefactorAgent

# 任務狀態儲存（單容器內有效）
tasks: Dict[str, Dict] = {}

# 日誌儲存（用於 stream）
task_logs: Dict[str, list] = {}

# 停止標誌（用於中斷執行）
stop_flags: Dict[str, bool] = {}

# Chat Agent 實例快取（以 thread_id 為 key，支援多輪對話）
chat_agents: Dict[str, "RefactorAgent"] = {}

# Refactor Agent 實例快取（以 thread_id 為 key，支援會話持久化）
refactor_agents: Dict[str, "RefactorAgent"] = {}

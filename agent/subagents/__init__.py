"""Agent Subagents - 子代理模組

所有在此模組中 import 的 subagent 都會自動註冊到 registry。
新增 subagent 時，只需在對應檔案中使用 register_subagent() 並在此處 import。
"""

# Import subagents（會自動觸發 register_subagent 註冊）
from agent.subagents import env_setup  # noqa: F401

# 為了向後相容，導出 DEFAULT_SUBAGENTS
from agent.registry import get_all_subagents


def load_all_subagents():
    """確保所有 subagents 已載入並註冊到 registry

    此函數在 deep_agent.py 初始化時呼叫，
    確保所有 subagent 模組都已被 import。
    """
    # 目前透過上方的 import 已自動載入
    # 未來可以改用 importlib 動態掃描資料夾
    pass


# 向後相容：提供 DEFAULT_SUBAGENTS
@property
def DEFAULT_SUBAGENTS():
    """向後相容：取得所有已註冊的 subagents"""
    return get_all_subagents()

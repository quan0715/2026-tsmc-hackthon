"""Agent Tools - 自定義工具模組

所有在此模組中 import 的 tool 都會自動註冊到 registry。
新增 tool 時，只需在此處 import 即可。
"""

# Import tools（會自動觸發 @register_tool decorator 註冊）
from agent.tools.bash import bash

# 導出所有 tools
__all__ = ["bash"]


def load_all_tools():
    """確保所有 tools 已載入並註冊到 registry

    此函數在 deep_agent.py 初始化時呼叫，
    確保所有 tool 模組都已被 import。
    """
    # 目前透過上方的 import 已自動載入
    # 未來可以改用 importlib 動態掃描資料夾
    pass

"""Registry 模組 - 集中管理 tools 和 subagents"""

from dataclasses import dataclass
from typing import Callable, Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class ToolConfig:
    """Tool 完整配置"""
    name: str
    func: Callable
    description: str = ""
    test: Optional[Callable] = None


@dataclass
class SubagentConfig:
    """Subagent 完整配置"""
    name: str
    description: str
    system_prompt: str
    tools: List[Callable]


# === 全域 Registry ===
_tool_registry: Dict[str, ToolConfig] = {}
_subagent_registry: Dict[str, Dict[str, Any]] = {}


def register_tool(
    name: str = None,
    description: str = None,
    test: Callable = None,
):
    """Decorator 註冊 tool 並附加 metadata

    Args:
        name: 工具名稱（預設使用函數名）
        description: 工具描述（注入 system_prompt）
        test: 測試函數（驗證工具是否正常運作）

    Example:
        @register_tool(
            description="執行 bash 命令",
            test=lambda: assert "test" in bash(command="echo test")
        )
        def bash(command: str) -> str:
            ...
    """
    def decorator(func: Callable) -> Callable:
        tool_name = name or func.__name__
        # description 優先順序: 參數 > docstring
        tool_desc = description or func.__doc__ or ""

        config = ToolConfig(
            name=tool_name,
            func=func,
            description=tool_desc,
            test=test,
        )
        _tool_registry[tool_name] = config
        logger.debug(f"註冊 tool: {tool_name}")
        return func
    return decorator


def register_subagent(config: Dict[str, Any]):
    """註冊 subagent

    Args:
        config: Subagent 配置字典，必須包含:
            - name: subagent 名稱
            - description: 描述
            - system_prompt: system prompt
            - tools: 工具列表

    Example:
        register_subagent({
            "name": "env-setup",
            "description": "環境設置專家",
            "system_prompt": "你是一個環境設置專家...",
            "tools": [bash],
        })
    """
    _subagent_registry[config["name"]] = config
    logger.debug(f"註冊 subagent: {config['name']}")


# === 取得 Registry 內容 ===

def get_all_tools() -> List[Callable]:
    """取得所有 tool 函數（用於傳給 create_deep_agent）"""
    return [cfg.func for cfg in _tool_registry.values()]


def get_all_tool_configs() -> List[ToolConfig]:
    """取得所有 tool 完整配置"""
    return list(_tool_registry.values())


def get_tool(name: str) -> Optional[Callable]:
    """取得特定 tool 函數"""
    config = _tool_registry.get(name)
    return config.func if config else None


def get_tool_config(name: str) -> Optional[ToolConfig]:
    """取得特定 tool 配置"""
    return _tool_registry.get(name)


def get_tool_descriptions() -> str:
    """產生所有 tool 的描述（用於注入 system_prompt）

    Returns:
        格式化的 tool 描述文字
    """
    if not _tool_registry:
        return ""

    lines = ["## 可用工具\n"]
    for cfg in _tool_registry.values():
        lines.append(f"### {cfg.name}\n")
        if cfg.description:
            lines.append(f"{cfg.description.strip()}\n")
        lines.append("")
    return "\n".join(lines)


def get_all_subagents() -> List[Dict[str, Any]]:
    """取得所有 subagent 配置（用於傳給 create_deep_agent）"""
    return list(_subagent_registry.values())


def get_subagent(name: str) -> Optional[Dict[str, Any]]:
    """取得特定 subagent 配置"""
    return _subagent_registry.get(name)


# === 測試功能 ===

def run_all_tool_tests() -> Dict[str, Optional[bool]]:
    """執行所有 tool 測試

    Returns:
        Dict[tool_name, result]:
            - True: 測試通過
            - False: 測試失敗
            - None: 無測試函數
    """
    results = {}
    for name, cfg in _tool_registry.items():
        if cfg.test:
            try:
                cfg.test()
                results[name] = True
                logger.info(f"Tool test passed: {name}")
            except Exception as e:
                results[name] = False
                logger.error(f"Tool test failed: {name} - {e}")
        else:
            results[name] = None
            logger.debug(f"Tool has no test: {name}")
    return results


def run_tool_test(name: str) -> Optional[bool]:
    """執行特定 tool 測試

    Returns:
        - True: 測試通過
        - False: 測試失敗
        - None: 無測試函數或 tool 不存在
    """
    cfg = _tool_registry.get(name)
    if not cfg:
        logger.warning(f"Tool not found: {name}")
        return None

    if not cfg.test:
        logger.debug(f"Tool has no test: {name}")
        return None

    try:
        cfg.test()
        logger.info(f"Tool test passed: {name}")
        return True
    except Exception as e:
        logger.error(f"Tool test failed: {name} - {e}")
        return False


# === 清除 Registry（用於測試）===

def clear_registry():
    """清除所有註冊的 tools 和 subagents（主要用於測試）"""
    _tool_registry.clear()
    _subagent_registry.clear()
    logger.debug("Registry cleared")


# === 列出 Registry 內容（用於除錯）===

def list_registered_tools() -> List[str]:
    """列出所有已註冊的 tool 名稱"""
    return list(_tool_registry.keys())


def list_registered_subagents() -> List[str]:
    """列出所有已註冊的 subagent 名稱"""
    return list(_subagent_registry.keys())

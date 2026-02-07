"""Deep Agent - MVP 版本 (Vertex AI + LangChain)"""
import logging
import os
from datetime import datetime
from typing import Optional, List, Callable, Dict, Any

from deepagents import create_deep_agent
from agent.models import AnthropicModelProvider
from agent.prompts import get_system_prompt
from deepagents.backends import FilesystemBackend
from agent.chunk_parser import ChunkParser
from langchain_core.messages import BaseMessage

# === 載入並註冊所有 tools 和 subagents ===
# 這些 import 會觸發 @register_tool 和 register_subagent
import agent.tools  # noqa: F401
import agent.subagents  # noqa: F401

# 從 registry 取得
from agent.registry import get_all_tools, get_all_subagents

logger = logging.getLogger(__name__)

from langchain.agents.middleware import SummarizationMiddleware

# 預設技能目錄（相對於 backend root）
DEFAULT_SKILLS = ["/workspace/skills/"]


class RefactorAgent:
    def __init__(
        self,
        model=None,
        verbose: bool = True,
        stop_check_callback=None,
        postgres_url: Optional[str] = None,
        tools: Optional[List[Callable]] = None,
        skills: Optional[List[str]] = None,
        subagents: Optional[List[Dict[str, Any]]] = None,
        enable_code_execution: bool = True,
    ):
        """初始化 RefactorAgent

        Args:
            model: LLM 模型實例
            verbose: 是否顯示詳細的 chunk 解析資訊
            stop_check_callback: 可選的停止檢查回調函數，返回 True 表示應該停止
            postgres_url: PostgreSQL 連線 URL (必填，用於會話持久化)
            tools: 額外的自定義工具列表（會與預設工具合併）
            skills: 技能目錄列表（相對於 backend root）
            subagents: 自定義 subagents 列表（會與預設 subagents 合併）
            enable_code_execution: 是否啟用程式碼執行工具（預設 True）

        Raises:
            ValueError: 當 postgres_url 未提供時
            RuntimeError: 當 PostgreSQL 初始化失敗時
        """
        self.model = model
        self.verbose = verbose
        self.root_dir = "/"
        self.stop_check_callback = stop_check_callback
        self.enable_code_execution = enable_code_execution

        # 檢查 postgres_url 必填
        if not postgres_url:
            raise ValueError(
                "PostgreSQL URL is required for persistence. "
                "Please set POSTGRES_URL environment variable."
            )
        self.postgres_url = postgres_url

        # 設定工具（從 registry 取得）
        self.tools = []
        if enable_code_execution:
            self.tools.extend(get_all_tools())
        if tools:
            self.tools.extend(tools)

        # 設定技能
        self.skills = skills if skills is not None else DEFAULT_SKILLS

        # 設定 subagents（從 registry 取得）
        self.subagents = list(get_all_subagents())
        if subagents:
            self.subagents.extend(subagents)

        # 初始化持久化後端（必須成功）
        self._setup_persistence()
        self._agent_init()

    def _setup_persistence(self):
        """設置 PostgreSQL 持久化後端（必須成功，不允許 fallback）

        參考: https://docs.langchain.com/oss/python/langgraph/add-memory

        Raises:
            RuntimeError: 當缺少依賴套件或 PostgreSQL 連接失敗時
        """
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            from langgraph.store.postgres import PostgresStore
            import psycopg

            logger.info(f"初始化 PostgreSQL 持久化: {self.postgres_url}")

            # 建立並保持 PostgreSQL 連接
            # 注意：這個連接會在 Agent 實例的生命週期內保持開啟
            self._pg_conn = psycopg.connect(
                self.postgres_url,
                autocommit=True,
                prepare_threshold=0,
            )

            # 初始化 checkpointer
            self.checkpointer = PostgresSaver(self._pg_conn)
            self.checkpointer.setup()  # ⚠️ 必須呼叫 setup() 建立表格（首次使用）
            logger.info("✅ PostgresSaver 初始化成功")

            # 初始化 store（用於長期記憶）
            self.store = PostgresStore(self._pg_conn)
            self.store.setup()  # ⚠️ 必須呼叫 setup() 建立表格（首次使用）
            logger.info("✅ PostgresStore 初始化成功")

        except ImportError as e:
            logger.error(f"❌ 缺少 PostgreSQL 依賴套件: {e}")
            raise RuntimeError(
                "PostgreSQL persistence dependencies not installed. "
                "Please run: pip install langgraph-checkpoint-postgres psycopg[binary]"
            ) from e
        except Exception as e:
            logger.error(f"❌ PostgreSQL 初始化失敗: {e}")
            raise RuntimeError(
                f"Failed to initialize PostgreSQL persistence: {e}. "
                "Please check POSTGRES_URL and ensure PostgreSQL is running."
            ) from e

    def _agent_init(self):
        if not self.model:
            raise ValueError("model is not set")

        # 記錄工具、技能和 subagents 配置
        tool_names = [t.__name__ for t in self.tools]
        subagent_names = [s["name"] for s in self.subagents]
        logger.info(
            f"初始化 Agent - 工具: {tool_names}, "
            f"技能目錄: {self.skills}, "
            f"Subagents: {subagent_names}, "
            f"持久化: PostgreSQL (checkpointer + store)"
        )

        # middleware 由 create_deep_agent 在啟用 checkpointer 時自動管理
        middleware = []

        self.agent = create_deep_agent(
            model=self.model,
            memory=[
                f"{self.root_dir}memory/AGENTS.md",
            ],
            tools=self.tools,
            skills=self.skills,
            subagents=self.subagents,
            backend=FilesystemBackend(
                root_dir=self.root_dir,
                virtual_mode=True
            ),
            system_prompt=get_system_prompt("autonomous_v3"),
            checkpointer=self.checkpointer,
            store=self.store,
            middleware=middleware if middleware else None,
        )

    def _content_to_text(self, content: Any) -> str:
        """將 message content 轉為可顯示的文字"""
        if content is None:
            return ""
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    if "text" in item and isinstance(item["text"], str):
                        parts.append(item["text"])
                    elif "content" in item and isinstance(item["content"], str):
                        parts.append(item["content"])
                else:
                    parts.append(str(item))
            return "".join(parts)
        return str(content)

    def _normalize_messages(
        self,
        messages: List[BaseMessage],
        base_timestamp: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """將 LangChain messages 轉為前端可用格式"""
        if base_timestamp is not None and not isinstance(base_timestamp, str):
            timestamp = str(base_timestamp)
        else:
            timestamp = base_timestamp or datetime.utcnow().isoformat()
        tool_outputs: Dict[str, Dict[str, Any]] = {}
        for msg in messages:
            if getattr(msg, "type", None) == "tool":
                tool_call_id = getattr(msg, "tool_call_id", None)
                if tool_call_id:
                    tool_outputs[tool_call_id] = {
                        "content": self._content_to_text(getattr(msg, "content", "")),
                        "name": getattr(msg, "name", None),
                        "id": getattr(msg, "id", None),
                    }

        normalized: List[Dict[str, Any]] = []
        used_tool_calls = set()
        for idx, msg in enumerate(messages):
            msg_type = getattr(msg, "type", None)

            if msg_type == "tool":
                tool_call_id = getattr(msg, "tool_call_id", None)
                if tool_call_id in used_tool_calls:
                    continue
                if tool_call_id:
                    used_tool_calls.add(tool_call_id)
                normalized.append(
                    {
                        "id": getattr(msg, "id", None) or f"tool-{idx}",
                        "role": "tool",
                        "content": "",
                        "timestamp": timestamp,
                        "toolName": getattr(msg, "name", None),
                        "toolCallId": tool_call_id,
                        "toolInput": None,
                        "toolOutput": self._content_to_text(getattr(msg, "content", "")),
                    }
                )
                continue

            role = {
                "human": "user",
                "ai": "assistant",
                "system": "system",
            }.get(msg_type, "assistant")

            normalized.append(
                {
                    "id": getattr(msg, "id", None) or f"{role}-{idx}",
                    "role": role,
                    "content": self._content_to_text(getattr(msg, "content", "")),
                    "timestamp": timestamp,
                }
            )

            if msg_type == "ai":
                tool_calls = getattr(msg, "tool_calls", None) or []
                for call in tool_calls:
                    tool_call_id = call.get("id") or f"tool-{idx}-{len(used_tool_calls)}"
                    used_tool_calls.add(tool_call_id)
                    output = tool_outputs.get(tool_call_id)
                    normalized.append(
                        {
                            "id": f"tool-{tool_call_id}",
                            "role": "tool",
                            "content": "",
                            "timestamp": timestamp,
                            "toolName": call.get("name"),
                            "toolCallId": tool_call_id,
                            "toolInput": call.get("args") or {},
                            "toolOutput": output.get("content") if output else None,
                        }
                    )

        return normalized

    def get_thread_history(
        self,
        thread_id: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """取得指定 thread 的聊天歷史"""
        # 簡化檢查（因為 __init__ 已確保 checkpointer 必定存在）
        assert self.checkpointer is not None, "Checkpointer should be initialized"

        config = {"configurable": {"thread_id": thread_id}}
        snapshot = self.agent.get_state(config)
        messages = snapshot.values.get("messages", []) if snapshot else []
        normalized = self._normalize_messages(messages, snapshot.created_at if snapshot else None)
        if limit and limit > 0:
            return normalized[-limit:]
        return normalized

    def run(
        self,
        user_message: str = "檢視我的專案資料夾結構",
        event_callback=None,
        thread_id: Optional[str] = None,
    ):
        """執行 Agent 並使用 ChunkParser 解析串流輸出

        Args:
            user_message: 使用者訊息
            event_callback: 可選的回調函數，用於處理每個解析事件
                          函數簽名: callback(event_type: str, data: dict)
            thread_id: 對話線程 ID，用於多輪對話持久化
        """
        # 初始化 ChunkParser（傳入 callback）
        parser = ChunkParser(verbose=self.verbose, event_callback=event_callback)

        print(f"\n{'='*60}", flush=True)
        print(f"🚀 開始執行 Agent", flush=True)
        if thread_id:
            print(f"📍 Thread ID: {thread_id}", flush=True)
        print(f"{'='*60}\n", flush=True)
        print(f"📝 User Message: {user_message}\n", flush=True)
        print(f"{'─'*60}", flush=True)
        print(f"💬 AI Response:\n", flush=True)

        # 設置配置（包含 thread_id）
        config = {}
        if thread_id:
            config = {"configurable": {"thread_id": thread_id}}

        # 串流執行
        result = self.agent.stream(
            {
                "messages": [
                    {"role": "user", "content": user_message}
                ]
            },
            config=config,
        )

        # 使用 ChunkParser 解析每個 chunk
        try:
            for chunk in result:
                # 檢查是否應該停止
                if self.stop_check_callback and self.stop_check_callback():
                    print(f"\n{'='*60}", flush=True)
                    print(f"⏹️  檢測到停止信號，中斷 Agent 執行", flush=True)
                    print(f"{'='*60}\n", flush=True)
                    raise KeyboardInterrupt("Agent stopped by user")

                parser.parse(chunk)
        except KeyboardInterrupt:
            print(f"\n{'='*60}", flush=True)
            print(f"⏹️  Agent 執行已被中斷", flush=True)
            print(f"{'='*60}\n", flush=True)
            raise

        # 顯示總結
        parser.print_summary()


if __name__ == "__main__":
    # 初始化 LLM (根據環境變數 LLM_PROVIDER 自動選擇)
    provider = AnthropicModelProvider()
    model = provider.get_model()

    # 創建 Agent (verbose=True 會顯示詳細的 token usage, tool calls 等資訊)
    agent = RefactorAgent(model, verbose=True)
    message = """
    檢視我的資料夾結構，並整理一個將此專案重構成 typescript 的計畫，並將檔案寫入 ./memory/plan.md 檔案
    """
    # 執行 Agent
    agent.run(user_message=message)

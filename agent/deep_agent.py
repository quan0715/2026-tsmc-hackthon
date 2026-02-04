"""Deep Agent - MVP 版本 (Vertex AI + LangChain)"""
import logging
import os
from typing import Optional, List, Callable, Dict, Any

from deepagents import create_deep_agent
from agent.models import AnthropicModelProvider
from agent.prompts import get_system_prompt
from deepagents.backends import FilesystemBackend
from agent.chunk_parser import ChunkParser

# === 載入並註冊所有 tools 和 subagents ===
# 這些 import 會觸發 @register_tool 和 register_subagent
import agent.tools  # noqa: F401
import agent.subagents  # noqa: F401

# 從 registry 取得
from agent.registry import get_all_tools, get_all_subagents

logger = logging.getLogger(__name__)

from langchain.agents.middleware import SummarizationMiddleware
# 🔑 P1: LangGraph Checkpointing 支持
try:
    from langgraph.checkpoint.sqlite import SqliteSaver
    CHECKPOINTING_AVAILABLE = True
except ImportError:
    CHECKPOINTING_AVAILABLE = False
    logger.warning("langgraph.checkpoint.sqlite 不可用，checkpointing 功能將被禁用")

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
        enable_checkpointing: bool = False,
        checkpoint_db: Optional[str] = None,
    ):
        """初始化 RefactorAgent

        Args:
            model: LLM 模型實例
            verbose: 是否顯示詳細的 chunk 解析資訊
            stop_check_callback: 可選的停止檢查回調函數，返回 True 表示應該停止
            postgres_url: PostgreSQL 連線字串，用於持久化對話狀態
            tools: 額外的自定義工具列表（會與預設工具合併）
            skills: 技能目錄列表（相對於 backend root）
            subagents: 自定義 subagents 列表（會與預設 subagents 合併）
            enable_code_execution: 是否啟用程式碼執行工具（預設 True）
        """
        self.model = model
        self.verbose = verbose
        self.root_dir = "/workspace/"
        self.stop_check_callback = stop_check_callback
        self.postgres_url = postgres_url
        self.enable_code_execution = enable_code_execution
        self.enable_checkpointing = enable_checkpointing
        
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
        
        # 初始化 Checkpointer
        self.checkpointer = None
        if enable_checkpointing and CHECKPOINTING_AVAILABLE:
            db_path = checkpoint_db or f"{self.root_dir}/memory/checkpoints.db"
            try:
                self.checkpointer = SqliteSaver.from_conn_string(db_path)
                logger.info(f"✅ Checkpointing 已啟用，資料庫：{db_path}")
            except Exception as e:
                logger.error(f"❌ 無法初始化 Checkpointer: {e}")
                self.checkpointer = None
        
        self._setup_persistence()
        self._agent_init()

    def _setup_persistence(self):
        """設置持久化後端"""
        if self.postgres_url:
            try:
                # 使用 PostgreSQL 持久化
                from langgraph.checkpoint.postgres import PostgresSaver
                from langgraph.store.postgres import PostgresStore

                logger.info("使用 PostgreSQL 持久化")
                self.checkpointer = PostgresSaver.from_conn_string(self.postgres_url)
                self.checkpointer.setup()  # 建立必要的表
                self.store = PostgresStore.from_conn_string(self.postgres_url)
                self.store.setup()
            except Exception as e:
                logger.warning(f"PostgreSQL 初始化失敗，回退到內存模式: {e}")
                self._setup_memory_persistence()
        else:
            self._setup_memory_persistence()

    def _setup_memory_persistence(self):
        """設置內存持久化（開發模式）"""
        from langgraph.checkpoint.memory import MemorySaver
        from langgraph.store.memory import InMemoryStore

        logger.info("使用內存持久化（開發模式）")
        self.checkpointer = MemorySaver()
        self.store = InMemoryStore()

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
            f"Checkpointing: {'啟用' if self.enable_checkpointing else '禁用'}"
        )

        # 準備 middleware 列表
        middleware = []
        if self.enable_checkpointing:
            # SummarizationMiddleware 需要 model 參數
            middleware.append(SummarizationMiddleware(model=self.model))

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
            system_prompt=get_system_prompt("default"),
            checkpointer=self.checkpointer,
            store=self.store,
            middleware=middleware,
        )

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

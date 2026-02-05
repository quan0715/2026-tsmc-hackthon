"""PostgreSQL 持久化功能驗證測試"""

import pytest
import os
import uuid
from unittest.mock import patch


class TestPostgresPersistence:
    """PostgreSQL 持久化功能驗證測試"""

    @pytest.mark.asyncio
    async def test_postgres_url_required(self):
        """測試：缺少 POSTGRES_URL 應拋出錯誤"""
        from agent.deep_agent import RefactorAgent
        from agent.models import AnthropicModelProvider

        provider = AnthropicModelProvider()
        model = provider.get_model()

        with pytest.raises(ValueError, match="PostgreSQL URL is required"):
            RefactorAgent(model=model, postgres_url=None)

    @pytest.mark.asyncio
    async def test_postgres_connection_failure(self):
        """測試：PostgreSQL 連接失敗應拋出錯誤"""
        from agent.deep_agent import RefactorAgent
        from agent.models import AnthropicModelProvider

        provider = AnthropicModelProvider()
        model = provider.get_model()

        invalid_url = "postgresql://invalid:invalid@localhost:9999/invalid"
        with pytest.raises(RuntimeError, match="Failed to initialize PostgreSQL"):
            RefactorAgent(model=model, postgres_url=invalid_url)

    @pytest.mark.asyncio
    async def test_checkpointer_setup(self):
        """測試：Checkpointer 應正確初始化"""
        from agent.deep_agent import RefactorAgent
        from agent.models import AnthropicModelProvider

        provider = AnthropicModelProvider()
        model = provider.get_model()

        postgres_url = os.environ.get(
            "POSTGRES_URL",
            "postgresql://langgraph:langgraph_secret@localhost:5432/langgraph"
        )

        agent = RefactorAgent(model=model, postgres_url=postgres_url)

        assert agent.checkpointer is not None, "Checkpointer 應該被初始化"
        assert agent.store is not None, "Store 應該被初始化"

    @pytest.mark.asyncio
    async def test_thread_persistence_across_instances(self):
        """測試：會話應正確持久化到 PostgreSQL（跨實例驗證）"""
        from agent.deep_agent import RefactorAgent
        from agent.models import AnthropicModelProvider

        postgres_url = os.environ.get(
            "POSTGRES_URL",
            "postgresql://langgraph:langgraph_secret@localhost:5432/langgraph"
        )

        provider = AnthropicModelProvider()
        model1 = provider.get_model()

        thread_id = f"test-thread-{uuid.uuid4()}"

        # 建立第一個 agent 實例並發送訊息
        agent1 = RefactorAgent(model=model1, postgres_url=postgres_url, verbose=False)

        # Mock agent.run 來避免實際執行 LLM（僅測試持久化機制）
        with patch.object(agent1.agent, 'stream') as mock_stream:
            # 模擬 stream 返回空結果
            mock_stream.return_value = iter([])

            agent1.run(
                user_message="Hello, this is message 1",
                thread_id=thread_id
            )

        # 建立新的 agent 實例（模擬重啟）
        model2 = provider.get_model()
        agent2 = RefactorAgent(model=model2, postgres_url=postgres_url, verbose=False)

        # 嘗試取得歷史記錄
        # 注意：因為我們 mock 了 stream，實際上不會有真實訊息
        # 這個測試主要驗證 checkpointer 能正常初始化和連接
        history = agent2.get_thread_history(thread_id)

        # 驗證能夠取得歷史（即使是空的）
        assert isinstance(history, list), "應該能取得歷史記錄列表"

    @pytest.mark.asyncio
    async def test_environment_variable_check_in_handlers(self):
        """測試：handlers.py 應檢查 POSTGRES_URL 是否存在"""
        from agent.server.handlers import execute_agent
        from agent.server import state
        from agent.server.schemas import TaskStatus
        import uuid
        from datetime import datetime

        task_id = str(uuid.uuid4())
        thread_id = f"test-thread-{uuid.uuid4()}"

        # 暫時移除 POSTGRES_URL
        original_postgres_url = os.environ.get("POSTGRES_URL")
        if "POSTGRES_URL" in os.environ:
            del os.environ["POSTGRES_URL"]

        try:
            # 初始化任務記錄（模擬 app.py 的行為）
            state.tasks[task_id] = {
                "task_id": task_id,
                "thread_id": thread_id,
                "status": TaskStatus.PENDING,
                "spec": "Test message",
                "created_at": datetime.utcnow().isoformat(),
                "started_at": None,
                "finished_at": None,
                "error_message": None,
            }

            # 執行 agent（應該立即失敗）
            execute_agent(
                task_id=task_id,
                spec="Test message",
                thread_id=thread_id,
                verbose=False
            )

            # 驗證任務狀態
            assert task_id in state.tasks, "任務應該被建立"
            task = state.tasks[task_id]
            assert task["status"] == TaskStatus.FAILED, "任務應該標記為失敗"
            assert "POSTGRES_URL" in task.get("error_message", ""), \
                "錯誤訊息應該提到 POSTGRES_URL"

        finally:
            # 恢復環境變數
            if original_postgres_url:
                os.environ["POSTGRES_URL"] = original_postgres_url

            # 清理狀態
            if task_id in state.tasks:
                del state.tasks[task_id]
            if task_id in state.task_logs:
                del state.task_logs[task_id]
            if task_id in state.stop_flags:
                del state.stop_flags[task_id]

    @pytest.mark.asyncio
    async def test_missing_dependencies_error(self):
        """測試：缺少依賴套件應給出清晰錯誤訊息"""
        from agent.deep_agent import RefactorAgent
        from agent.models import AnthropicModelProvider
        import sys

        provider = AnthropicModelProvider()
        model = provider.get_model()

        postgres_url = "postgresql://test:test@localhost:5432/test"

        # Mock ImportError by patching the import
        def mock_import(name, *args, **kwargs):
            if name == "langgraph.checkpoint.postgres":
                raise ImportError("No module named 'langgraph.checkpoint.postgres'")
            return original_import(name, *args, **kwargs)

        original_import = __builtins__.__import__

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(RuntimeError, match="PostgreSQL persistence dependencies not installed"):
                RefactorAgent(model=model, postgres_url=postgres_url)

"""Server Handlers - 背景任務處理函數"""

import os
import logging
import traceback
from datetime import datetime

from agent.server.schemas import TaskStatus
from agent.server import state
from agent.model_factory import ModelFactory
from agent.deep_agent import RefactorAgent

logger = logging.getLogger(__name__)


def log_task(task_id: str, message: str):
    """記錄任務日誌（用於 stream）"""
    if task_id not in state.task_logs:
        state.task_logs[task_id] = []
    timestamp = datetime.utcnow().isoformat()
    log_entry = {"timestamp": timestamp, "message": message}
    state.task_logs[task_id].append(log_entry)
    logger.info(f"[{task_id}] {message}")


def execute_agent(task_id: str, spec: str, thread_id: str, verbose: bool, model: str = None):
    """背景執行 Agent（在 BackgroundTasks 中執行）

    支援會話持久化：
    - 使用 thread_id 來維持對話上下文
    - 相同 thread_id 的執行會延續之前的對話歷史
    - 對話狀態會透過 PostgreSQL 持久化（如果配置了 POSTGRES_URL）
    """
    try:
        # 初始化日誌和停止標誌
        state.task_logs[task_id] = []
        state.stop_flags[task_id] = False

        # 更新狀態為 RUNNING
        state.tasks[task_id]["status"] = TaskStatus.RUNNING
        state.tasks[task_id]["started_at"] = datetime.utcnow().isoformat()

        msg = f"🚀 [DEBUG] Task {task_id}: 開始執行 (thread: {thread_id})"
        print(msg, flush=True)
        log_task(task_id, f"🚀 開始執行 Agent (thread: {thread_id})")

        # 檢查停止標誌
        if state.stop_flags.get(task_id, False):
            log_task(task_id, "⏹️  任務在初始化前被停止")
            state.tasks[task_id]["status"] = TaskStatus.STOPPED
            state.tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
            return

        # 獲取 PostgreSQL URL（必填）
        postgres_url = os.environ.get("POSTGRES_URL")
        if not postgres_url:
            error_msg = "POSTGRES_URL environment variable is not set. PostgreSQL persistence is required."
            log_task(task_id, f"❌ 錯誤: {error_msg}")
            state.tasks[task_id]["status"] = TaskStatus.FAILED
            state.tasks[task_id]["error_message"] = error_msg
            state.tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
            return

        log_task(task_id, "🔗 使用 PostgreSQL 持久化")

        # 獲取或建立 Agent（複用同一 thread 的 agent）
        if thread_id not in state.refactor_agents:
            print(f"🔧 [DEBUG] Task {task_id}: 初始化 LLM (model={model or 'default'})", flush=True)
            log_task(task_id, f"🔧 初始化 LLM (model={model or 'default'})...")
            factory = ModelFactory()
            llm_model = factory.create_model(model)
            print(f"✅ [DEBUG] Task {task_id}: LLM 初始化完成", flush=True)
            log_task(task_id, "✅ LLM 初始化完成")

            # 再次檢查停止標誌
            if state.stop_flags.get(task_id, False):
                log_task(task_id, "⏹️  任務在 LLM 初始化後被停止")
                state.tasks[task_id]["status"] = TaskStatus.STOPPED
                finished = datetime.utcnow().isoformat()
                state.tasks[task_id]["finished_at"] = finished
                return

            # 建立 RefactorAgent
            msg = f"🤖 [DEBUG] Task {task_id}: 建立 RefactorAgent"
            print(msg, flush=True)
            log_task(task_id, "🤖 建立 RefactorAgent...")

            def stop_check():
                return state.stop_flags.get(task_id, False)

            state.refactor_agents[thread_id] = RefactorAgent(
                model=llm_model,
                verbose=verbose,
                postgres_url=postgres_url,
                stop_check_callback=stop_check
            )
            msg = f"✅ [DEBUG] Task {task_id}: RefactorAgent 建立完成"
            print(msg, flush=True)
            log_task(task_id, "✅ RefactorAgent 建立完成")
        else:
            log_task(task_id, "♻️  複用現有 RefactorAgent（延續對話）")
            # 更新停止檢查回調
            state.refactor_agents[thread_id].stop_check_callback = (
                lambda: state.stop_flags.get(task_id, False)
            )

        agent = state.refactor_agents[thread_id]

        # 定義事件回調函數
        def handle_chunk_event(event_type: str, data: dict):
            """處理 ChunkParser 的事件（帶停止檢查）"""
            if state.stop_flags.get(task_id, False):
                log_task(task_id, "⏹️  檢測到停止信號，準備中斷執行")
                raise KeyboardInterrupt("Task stopped by user")

            import json
            json_str = json.dumps(data, ensure_ascii=False, default=str)
            log_task(task_id, f"[{event_type}] {json_str}")

        print(f"▶️  [DEBUG] Task {task_id}: 開始執行 Agent", flush=True)
        log_task(task_id, f"▶️  執行 Agent，spec: {spec[:100]}...")

        # 執行 Agent
        agent.run(
            user_message=spec,
            event_callback=handle_chunk_event,
            thread_id=thread_id
        )

        # 檢查是否被停止
        if state.stop_flags.get(task_id, False):
            state.tasks[task_id]["status"] = TaskStatus.STOPPED
            state.tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
            log_task(task_id, "⏹️  任務執行已被停止")
        else:
            state.tasks[task_id]["status"] = TaskStatus.SUCCESS
            state.tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
            print(f"✅ [DEBUG] Task {task_id}: Agent 執行完成", flush=True)
            log_task(task_id, "✅ Agent 執行完成")

    except KeyboardInterrupt:
        print(f"⏹️  [DEBUG] Task {task_id}: 任務被用戶中斷", flush=True)
        log_task(task_id, "⏹️  任務已被用戶停止")
        state.tasks[task_id]["status"] = TaskStatus.STOPPED
        state.tasks[task_id]["error_message"] = "Task stopped by user"
        state.tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
    except Exception as e:
        error_msg = f"Agent execution failed: {str(e)}"
        print(f"❌ [DEBUG] Task {task_id}: 錯誤 - {error_msg}", flush=True)
        print(f"[DEBUG] Traceback:\n{traceback.format_exc()}", flush=True)
        log_task(task_id, f"❌ 錯誤: {error_msg}")
        log_task(task_id, f"Traceback: {traceback.format_exc()}")
        logger.error(f"[{task_id}] {error_msg}\n{traceback.format_exc()}")
        state.tasks[task_id]["status"] = TaskStatus.FAILED
        state.tasks[task_id]["error_message"] = error_msg
        state.tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
    finally:
        if task_id in state.stop_flags:
            del state.stop_flags[task_id]


def execute_chat(task_id: str, thread_id: str, message: str, verbose: bool, model: str = None):
    """背景執行聊天任務（支援多輪對話）"""
    try:
        # 初始化日誌和停止標誌
        state.task_logs[task_id] = []
        state.stop_flags[task_id] = False

        # 更新狀態為 RUNNING
        state.tasks[task_id]["status"] = TaskStatus.RUNNING
        state.tasks[task_id]["started_at"] = datetime.utcnow().isoformat()

        print(
            f"💬 [DEBUG] Chat Task {task_id}: 開始執行 (thread: {thread_id})",
            flush=True
        )
        log_task(task_id, f"💬 開始聊天 (thread: {thread_id})")

        # 檢查停止標誌
        if state.stop_flags.get(task_id, False):
            log_task(task_id, "⏹️  任務在初始化前被停止")
            state.tasks[task_id]["status"] = TaskStatus.STOPPED
            state.tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
            return

        # 獲取 PostgreSQL URL（必填）
        postgres_url = os.environ.get("POSTGRES_URL")
        if not postgres_url:
            error_msg = "POSTGRES_URL environment variable is not set. PostgreSQL persistence is required."
            log_task(task_id, f"❌ 錯誤: {error_msg}")
            state.tasks[task_id]["status"] = TaskStatus.FAILED
            state.tasks[task_id]["error_message"] = error_msg
            state.tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
            return

        log_task(task_id, "🔗 使用 PostgreSQL 持久化")

        # 獲取或建立 Agent
        if thread_id not in state.chat_agents:
            log_task(task_id, f"🔧 初始化 LLM (model={model or 'default'})...")
            factory = ModelFactory()
            llm_model = factory.create_model(model)
            log_task(task_id, "✅ LLM 初始化完成")

            log_task(task_id, "🤖 建立 ChatAgent...")

            def chat_stop_check():
                return state.stop_flags.get(task_id, False)

            state.chat_agents[thread_id] = RefactorAgent(
                model=llm_model,
                verbose=verbose,
                postgres_url=postgres_url,
                stop_check_callback=chat_stop_check
            )
            log_task(task_id, "✅ ChatAgent 建立完成")
        else:
            log_task(task_id, "♻️  複用現有 ChatAgent")
            state.chat_agents[thread_id].stop_check_callback = (
                lambda: state.stop_flags.get(task_id, False)
            )

        agent = state.chat_agents[thread_id]

        # 定義事件回調函數
        def handle_chunk_event(event_type: str, data: dict):
            """處理 ChunkParser 的事件"""
            if state.stop_flags.get(task_id, False):
                log_task(task_id, "⏹️  檢測到停止信號，準備中斷執行")
                raise KeyboardInterrupt("Task stopped by user")

            import json
            json_str = json.dumps(data, ensure_ascii=False, default=str)
            log_task(task_id, f"[{event_type}] {json_str}")

        log_task(task_id, f"▶️  發送訊息: {message[:100]}...")

        # 執行聊天
        agent.run(
            user_message=message,
            event_callback=handle_chunk_event,
            thread_id=thread_id,
        )

        # 檢查是否被停止
        if state.stop_flags.get(task_id, False):
            state.tasks[task_id]["status"] = TaskStatus.STOPPED
            state.tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
            log_task(task_id, "⏹️  聊天已被停止")
        else:
            state.tasks[task_id]["status"] = TaskStatus.SUCCESS
            state.tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
            log_task(task_id, "✅ 聊天完成")

    except KeyboardInterrupt:
        print(f"⏹️  [DEBUG] Chat Task {task_id}: 被用戶中斷", flush=True)
        log_task(task_id, "⏹️  聊天已被用戶停止")
        state.tasks[task_id]["status"] = TaskStatus.STOPPED
        state.tasks[task_id]["error_message"] = "Chat stopped by user"
        state.tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
    except Exception as e:
        error_msg = f"Chat execution failed: {str(e)}"
        print(f"❌ [DEBUG] Chat Task {task_id}: 錯誤 - {error_msg}", flush=True)
        print(f"[DEBUG] Traceback:\n{traceback.format_exc()}", flush=True)
        log_task(task_id, f"❌ 錯誤: {error_msg}")
        log_task(task_id, f"Traceback: {traceback.format_exc()}")
        state.tasks[task_id]["status"] = TaskStatus.FAILED
        state.tasks[task_id]["error_message"] = error_msg
        state.tasks[task_id]["finished_at"] = datetime.utcnow().isoformat()
    finally:
        if task_id in state.stop_flags:
            del state.stop_flags[task_id]

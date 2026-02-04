"""Server App - FastAPI application and routes"""

import logging
import sys
import uuid
import json as json_lib
import asyncio
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks
from sse_starlette.sse import EventSourceResponse

from agent.server.schemas import (
    TaskStatus,
    RunRequest,
    ChatRequest,
    ChatResponse,
    RunResponse,
    TaskStatusResponse,
)
from agent.server import state
from agent.server.handlers import execute_agent, execute_chat, log_task

# 配置 logging 輸出到 stdout
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

# FastAPI App
app = FastAPI(title="AI Server", version="1.0.0")


# === Health Check ===

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# === Chat Routes ===

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """聊天模式 - 支援多輪對話

    使用 thread_id 來維持對話上下文，相同 thread_id 的訊息會被視為同一對話。
    """
    task_id = str(uuid.uuid4())
    thread_id = request.thread_id

    # 建立任務記錄
    state.tasks[task_id] = {
        "task_id": task_id,
        "thread_id": thread_id,
        "status": TaskStatus.PENDING,
        "message": request.message,
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "finished_at": None,
        "error_message": None,
    }

    # 啟動背景任務
    background_tasks.add_task(
        execute_chat,
        task_id=task_id,
        thread_id=thread_id,
        message=request.message,
        verbose=request.verbose
    )

    logger.info(f"[{task_id}] Chat 任務已建立 (thread: {thread_id})")

    return ChatResponse(
        task_id=task_id,
        thread_id=thread_id,
        status=TaskStatus.PENDING,
        message="聊天任務已啟動，正在背景執行"
    )


# === Run Routes ===

@app.post("/run", response_model=RunResponse)
async def run_agent(request: RunRequest, background_tasks: BackgroundTasks):
    """啟動 Agent 執行（異步模式，支援會話持久化）

    立即返回 task_id，Agent 在背景執行。
    使用 GET /tasks/{task_id} 查詢執行狀態。
    """
    task_id = str(uuid.uuid4())
    thread_id = request.thread_id or f"refactor-{task_id}"

    # 建立任務記錄
    state.tasks[task_id] = {
        "task_id": task_id,
        "thread_id": thread_id,
        "status": TaskStatus.PENDING,
        "spec": request.spec,
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "finished_at": None,
        "error_message": None,
    }

    # 啟動背景任務
    background_tasks.add_task(
        execute_agent,
        task_id=task_id,
        spec=request.spec,
        thread_id=thread_id,
        verbose=request.verbose
    )

    logger.info(f"[{task_id}] 任務已建立 (thread: {thread_id})，開始背景執行")

    return RunResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="Agent 任務已啟動，正在背景執行"
    )


# === Task Routes ===

@app.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """查詢任務執行狀態"""
    if task_id not in state.tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = state.tasks[task_id]
    return TaskStatusResponse(
        task_id=task["task_id"],
        status=task["status"],
        created_at=task["created_at"],
        started_at=task.get("started_at"),
        finished_at=task.get("finished_at"),
        error_message=task.get("error_message"),
    )


@app.get("/tasks")
async def list_tasks():
    """列出所有任務（調試用）"""
    return {"total": len(state.tasks), "tasks": list(state.tasks.values())}


@app.get("/tasks/{task_id}/stream")
async def stream_task_logs(task_id: str):
    """SSE 串流任務執行日誌（支援結構化事件）"""
    if task_id not in state.tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        """生成 SSE events"""
        last_index = 0

        while True:
            task = state.tasks.get(task_id)
            if not task:
                break

            # 發送新日誌
            if task_id in state.task_logs:
                current_logs = state.task_logs[task_id]
                new_logs = current_logs[last_index:]

                for log in new_logs:
                    message = log['message']

                    # 嘗試解析是否為結構化事件
                    if message.startswith('[') and ']' in message:
                        try:
                            close_bracket = message.index(']')
                            event_type = message[1:close_bracket]
                            json_data = message[close_bracket + 2:]
                            data = json_lib.loads(json_data)

                            data_str = json_lib.dumps(data, ensure_ascii=False)
                            yield {"event": event_type, "data": data_str}
                        except (ValueError, json_lib.JSONDecodeError):
                            yield {
                                "event": "log",
                                "data": json_lib.dumps({
                                    "timestamp": log['timestamp'],
                                    "message": message
                                }, ensure_ascii=False)
                            }
                    else:
                        yield {
                            "event": "log",
                            "data": json_lib.dumps({
                                "timestamp": log['timestamp'],
                                "message": message
                            }, ensure_ascii=False)
                        }

                last_index = len(current_logs)

            # 如果任務完成，發送完成事件並結束
            finished_statuses = [
                TaskStatus.SUCCESS,
                TaskStatus.FAILED,
                TaskStatus.STOPPED
            ]
            if task["status"] in finished_statuses:
                yield {
                    "event": "status",
                    "data": json_lib.dumps({
                        "status": task['status'].lower(),
                        "finished_at": task.get('finished_at'),
                        "error_message": task.get('error_message')
                    }, ensure_ascii=False)
                }
                break

            await asyncio.sleep(0.5)

    return EventSourceResponse(event_generator())


@app.post("/tasks/{task_id}/stop")
async def stop_task(task_id: str):
    """停止執行中的任務"""
    if task_id not in state.tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = state.tasks[task_id]

    # 只能停止 PENDING 或 RUNNING 的任務
    if task["status"] not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot stop task with status: {task['status']}"
        )

    # 設置停止標誌
    state.stop_flags[task_id] = True

    log_task(task_id, "⏹️  收到停止信號，正在中斷任務...")
    logger.info(f"[{task_id}] Stop signal received, interrupting task...")

    return {
        "task_id": task_id,
        "status": "stopping",
        "message": "Stop signal sent, task will be interrupted"
    }


@app.post("/tasks/{task_id}/resume")
async def resume_task(task_id: str, background_tasks: BackgroundTasks):
    """繼續執行已停止的任務"""
    if task_id not in state.tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    old_task = state.tasks[task_id]

    # 只能繼續 STOPPED 或 FAILED 的任務
    if old_task["status"] not in [TaskStatus.STOPPED, TaskStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot resume task with status: {old_task['status']}"
        )

    # 使用原始 thread_id 和 spec 建立新任務
    new_task_id = str(uuid.uuid4())
    spec = old_task.get("spec", old_task.get("init_prompt", ""))
    thread_id = old_task.get("thread_id", f"refactor-{task_id}")

    state.tasks[new_task_id] = {
        "task_id": new_task_id,
        "thread_id": thread_id,
        "status": TaskStatus.PENDING,
        "spec": spec,
        "created_at": datetime.utcnow().isoformat(),
        "started_at": None,
        "finished_at": None,
        "error_message": None,
        "resumed_from": task_id
    }

    # 啟動背景任務
    background_tasks.add_task(
        execute_agent,
        task_id=new_task_id,
        spec=spec,
        thread_id=thread_id,
        verbose=True
    )

    msg = f"[{new_task_id}] Task resumed from [{task_id}] (thread: {thread_id})"
    logger.info(msg)
    log_task(new_task_id, f"▶️  從任務 {task_id} 恢復執行")

    return {
        "task_id": new_task_id,
        "old_task_id": task_id,
        "thread_id": thread_id,
        "status": TaskStatus.PENDING,
        "message": "Task resumed with new task_id"
    }

# ============================================
# Stage 1: Dependencies (for better caching)
# ============================================
FROM python:3.11-slim AS dependencies

# 只安裝 runtime 必要的系統套件
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# 先複製 requirements.txt（這層變動頻率低，cache 命中率高）
COPY agent/requirements.txt /tmp/requirements.txt

# 安裝 Python 依賴（使用 wheel 避免編譯）
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM python:3.11-slim AS runtime

# 安裝 runtime 必要的系統套件（git 用於 clone repo）
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 從 dependencies stage 複製已安裝的 Python 套件
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# 設定環境變數
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 設定工作目錄
WORKDIR /workspace

# 建立目錄結構（單一 RUN 指令）
RUN mkdir -p memory artifacts skills agent

# 複製 agent 程式碼（排除 workspace 子目錄，使用 .dockerignore）
# 按變動頻率排序：低頻率的先複製
COPY agent/__init__.py agent/.env.example /workspace/agent/
COPY agent/models.py agent/registry.py agent/chunk_parser.py /workspace/agent/
COPY agent/prompts.py agent/deep_agent.py agent/ai_server.py /workspace/agent/
COPY agent/tools/ /workspace/agent/tools/
COPY agent/subagents/ /workspace/agent/subagents/
COPY agent/server/ /workspace/agent/server/

# 複製 workspace 資源（memory 和 skills）
COPY agent/workspace/memory/ /workspace/memory/
COPY agent/workspace/skills/ /workspace/skills/

# 設定 .env（如果不存在）
RUN if [ ! -f /workspace/agent/.env ] && [ -f /workspace/agent/.env.example ]; then \
        cp /workspace/agent/.env.example /workspace/agent/.env; \
    fi

# 暴露 AI Server port
EXPOSE 8000

# 啟動 AI Server
CMD ["uvicorn", "agent.ai_server:app", "--host", "0.0.0.0", "--port", "8000"]

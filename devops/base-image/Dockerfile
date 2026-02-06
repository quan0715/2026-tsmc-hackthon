# syntax=docker/dockerfile:1.7

# ============================================
# Stage 1: Dependencies (for better caching)
# ============================================
FROM python:3.11-slim AS dependencies

# Keep pip quiet and deterministic-ish (and avoid extra network calls for version checks).
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_PYTHON_VERSION_WARNING=1

# 只安裝 runtime 必要的系統套件與工具鏈
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt/lists,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
      ca-certificates \
      curl \
      git \
      gnupg \
      lsb-release \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://packages.adoptium.net/artifactory/api/gpg/key/public \
      | gpg --dearmor -o /etc/apt/keyrings/adoptium.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/adoptium.gpg] https://packages.adoptium.net/artifactory/deb \
      $(. /etc/os-release && echo $VERSION_CODENAME) main" \
      > /etc/apt/sources.list.d/adoptium.list \
    && apt-get update && apt-get install -y --no-install-recommends \
      golang-go \
      temurin-17-jdk \
      kotlin \
      postgresql-client \
      nodejs \
      npm \
    && rm -rf /var/lib/apt/lists/*

# 先複製 requirements.txt（這層變動頻率低，cache 命中率高）
COPY agent/requirements.txt /tmp/requirements.txt

# 安裝 Python 依賴（使用 wheel 避免編譯）
RUN --mount=type=cache,target=/root/.cache/pip,sharing=locked \
    pip install --prefer-binary -r /tmp/requirements.txt

# ============================================
# Stage 2: Runtime
# ============================================
FROM dependencies AS runtime

# 設定環境變數
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# 設定工作目錄
WORKDIR /workspace

# 建立目錄結構（單一 RUN 指令）
RUN mkdir -p memory artifacts skills agent

# 複製 agent 程式碼
COPY agent/ /workspace/agent/

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

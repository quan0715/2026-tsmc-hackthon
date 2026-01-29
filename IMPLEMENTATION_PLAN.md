# AI 舊程式碼智能重構系統 - 實作計劃

## 專案概述

打造一個智能重構程式碼系統，能分步驟且用多次迭代的方式，將舊專案翻新成現代化專案。系統需要提供隔離的執行環境、即時日誌串流、指令執行等功能。

## 技術棧

### 後端框架
- **FastAPI**: 現代化的 Python Web 框架，支援非同步操作和自動 API 文件生成
- **Python 3.11+**: 最新的 Python 版本，效能更好

### 資料庫
- **MongoDB**: NoSQL 資料庫，適合儲存靈活的專案資料和日誌
- **Motor**: MongoDB 的非同步驅動程式

### 容器管理
- **Docker SDK for Python**: 管理 Docker 容器的生命週期
- **Docker Compose**: 本地開發環境編排

### 其他工具
- **Pydantic**: 資料驗證和序列化
- **SSE-Starlette**: Server-Sent Events 支援
- **pytest**: 測試框架
- **GitPython**: Git 操作

## 專案結構

```
auto-refactor-agent/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI 應用入口
│   ├── config.py               # 配置管理
│   ├── models/                 # Pydantic 模型
│   │   ├── __init__.py
│   │   ├── project.py          # 專案模型
│   │   └── execution.py        # 執行結果模型
│   ├── schemas/                # API Schema
│   │   ├── __init__.py
│   │   ├── project.py
│   │   └── execution.py
│   ├── services/               # 業務邏輯
│   │   ├── __init__.py
│   │   ├── project_service.py
│   │   ├── container_service.py
│   │   └── log_service.py
│   ├── routers/                # API 路由
│   │   ├── __init__.py
│   │   ├── projects.py
│   │   └── health.py
│   └── database/               # 資料庫連接
│       ├── __init__.py
│       └── mongodb.py
├── tests/                      # 測試
│   ├── __init__.py
│   ├── test_api.py
│   └── test_services.py
├── docker/
│   ├── Dockerfile              # API 服務 Dockerfile
│   └── base-image/             # 基礎容器映像
│       └── Dockerfile
├── scripts/
│   └── init_db.py              # 資料庫初始化腳本
├── docker-compose.yml          # 本地開發環境
├── requirements.txt            # Python 依賴
├── .env.example                # 環境變數範例
├── .gitignore
└── README.md
```

## 資料庫 Schema

### Project Collection

```javascript
{
  _id: ObjectId,
  repo_url: String,           // Git repository URL
  branch: String,             // Git branch name
  init_prompt: String,        // 初始化提示
  status: String,             // CREATED, PROVISIONING, READY, RUNNING, STOPPED, FAILED, DELETED
  container_id: String,       // Docker container ID
  container_name: String,     // Docker container name
  last_error: String,         // 最後錯誤訊息
  created_at: DateTime,
  updated_at: DateTime,
  metadata: Object            // 額外的 metadata
}
```

### Logs Collection (Optional - 可儲存歷史 logs)

```javascript
{
  _id: ObjectId,
  project_id: ObjectId,
  timestamp: DateTime,
  level: String,              // INFO, ERROR, WARNING
  message: String,
  source: String              // provision, exec, system
}
```

## API 設計

### MVP-1: 專案建立 API + DB

#### POST /api/v1/projects
建立新專案

**Request Body:**
```json
{
  "repo_url": "https://github.com/user/repo.git",
  "branch": "main",
  "init_prompt": "Refactor this project to use modern Python practices"
}
```

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "repo_url": "https://github.com/user/repo.git",
  "branch": "main",
  "init_prompt": "Refactor this project to use modern Python practices",
  "status": "CREATED",
  "created_at": "2026-01-29T05:00:00Z",
  "updated_at": "2026-01-29T05:00:00Z"
}
```

#### GET /api/v1/projects/{id}
查詢專案詳情

**Response:**
```json
{
  "id": "507f1f77bcf86cd799439011",
  "repo_url": "https://github.com/user/repo.git",
  "branch": "main",
  "init_prompt": "Refactor this project to use modern Python practices",
  "status": "READY",
  "container_id": "abc123def456",
  "container_name": "refactor-project-abc123",
  "docker_status": {
    "state": "running",
    "started_at": "2026-01-29T05:01:00Z"
  },
  "created_at": "2026-01-29T05:00:00Z",
  "updated_at": "2026-01-29T05:01:30Z"
}
```

### MVP-2: Provision API

#### POST /api/v1/projects/{id}/provision
建立容器並 clone repository

**Response:**
```json
{
  "status": "PROVISIONING",
  "message": "Container provisioning started"
}
```

### MVP-3: Exec 指令 API

#### POST /api/v1/projects/{id}/exec
執行指令

**Request Body:**
```json
{
  "command": "ls -la",
  "workdir": "/workspace/repo"
}
```

**Response:**
```json
{
  "stdout": "total 12\ndrwxr-xr-x 3 root root 4096 ...",
  "stderr": "",
  "exit_code": 0,
  "execution_time_ms": 45
}
```

### MVP-4: Logs SSE 串流

#### GET /api/v1/projects/{id}/logs/stream
SSE 串流日誌

**Query Parameters:**
- `follow`: boolean (default: true) - 是否持續 follow
- `tail`: number (default: 100) - 顯示最後幾行

**SSE Event Format:**
```
event: log
data: {"timestamp": "2026-01-29T05:00:00Z", "level": "INFO", "message": "Cloning repository..."}

event: log
data: {"timestamp": "2026-01-29T05:00:01Z", "level": "INFO", "message": "Repository cloned successfully"}

event: ping
data: {"timestamp": "2026-01-29T05:00:30Z"}
```

### MVP-5: Container Lifecycle

#### POST /api/v1/projects/{id}/stop
停止容器

**Response:**
```json
{
  "status": "STOPPED",
  "message": "Container stopped successfully"
}
```

#### DELETE /api/v1/projects/{id}
刪除專案和容器

**Response:**
```json
{
  "status": "DELETED",
  "message": "Project and container deleted successfully"
}
```

### MVP-6: 失敗回滾與狀態一致性

自動處理：
- Provision 失敗時，自動設定 status=FAILED
- 記錄 last_error
- 清理已建立的容器
- GET /projects/{id} 回傳完整狀態資訊

## 實作步驟

### Phase 1: 專案基礎架構 (Task #1)

1. **建立專案目錄結構**
   - 建立上述的目錄結構
   - 設定 Python 虛擬環境

2. **配置依賴管理**
   - 建立 `requirements.txt`
   - 安裝核心依賴：
     - fastapi[all]
     - motor
     - docker
     - pydantic-settings
     - sse-starlette
     - gitpython
     - pytest
     - pytest-asyncio

3. **環境變數配置**
   - 建立 `.env.example`
   - 配置項：
     - MONGODB_URL
     - DATABASE_NAME
     - DOCKER_BASE_IMAGE
     - API_HOST
     - API_PORT
     - LOG_LEVEL

4. **Docker 配置**
   - 建立 `docker-compose.yml` (MongoDB + API)
   - 建立基礎映像 Dockerfile
   - 建立 API 服務 Dockerfile

5. **基礎程式碼**
   - 建立 FastAPI 應用
   - 設定 MongoDB 連接
   - 建立基礎配置管理
   - 設定 CORS 和中介軟體

### Phase 2: MVP-1 專案建立 API + DB (Task #2)

1. **資料模型**
   - 建立 `models/project.py`
   - 定義 Project Pydantic 模型
   - 定義 ProjectStatus Enum

2. **API Schema**
   - 建立 `schemas/project.py`
   - CreateProjectRequest
   - ProjectResponse

3. **Service Layer**
   - 建立 `services/project_service.py`
   - `create_project()`
   - `get_project_by_id()`
   - MongoDB CRUD 操作

4. **API Router**
   - 建立 `routers/projects.py`
   - POST /api/v1/projects
   - GET /api/v1/projects/{id}

5. **測試**
   - 單元測試
   - API 整合測試

### Phase 3: MVP-2 Provision (Task #3)

1. **Container Service**
   - 建立 `services/container_service.py`
   - Docker client 初始化
   - `create_container()` - 建立容器
   - `clone_repository()` - clone repo 到容器

2. **Provision Workflow**
   - 更新 `project_service.py`
   - `provision_project()` 方法
   - 狀態管理：PROVISIONING → READY

3. **API Router**
   - 更新 `routers/projects.py`
   - POST /api/v1/projects/{id}/provision

4. **錯誤處理**
   - 處理 Docker 錯誤
   - 處理 Git clone 錯誤

5. **測試**
   - Container 建立測試
   - Repository clone 測試

### Phase 4: MVP-3 Exec 指令 API (Task #4)

1. **Execution Service**
   - 更新 `services/container_service.py`
   - `exec_command()` - 在容器中執行指令
   - 捕獲 stdout/stderr/exit_code

2. **API Schema**
   - 建立 `schemas/execution.py`
   - ExecCommandRequest
   - ExecCommandResponse

3. **API Router**
   - 更新 `routers/projects.py`
   - POST /api/v1/projects/{id}/exec

4. **測試**
   - 指令執行測試
   - 錯誤處理測試

### Phase 5: MVP-4 Logs SSE 串流 (Task #5)

1. **Log Service**
   - 建立 `services/log_service.py`
   - `stream_logs()` - SSE 串流生成器
   - Docker logs API 整合
   - Ping mechanism

2. **SSE Implementation**
   - 使用 `sse-starlette`
   - 處理 client 斷線
   - 資源清理

3. **API Router**
   - 更新 `routers/projects.py`
   - GET /api/v1/projects/{id}/logs/stream

4. **測試**
   - SSE 連接測試
   - 斷線重連測試

### Phase 6: MVP-5 Container Lifecycle (Task #6)

1. **Container Management**
   - 更新 `services/container_service.py`
   - `stop_container()` - 停止容器
   - `remove_container()` - 刪除容器

2. **狀態同步**
   - 更新 `project_service.py`
   - `stop_project()` - 更新 DB status
   - `delete_project()` - 刪除 DB 記錄 + 容器

3. **API Router**
   - 更新 `routers/projects.py`
   - POST /api/v1/projects/{id}/stop
   - DELETE /api/v1/projects/{id}

4. **測試**
   - 停止容器測試
   - 刪除專案測試
   - 狀態同步測試

### Phase 7: MVP-6 失敗回滾與狀態一致性 (Task #7)

1. **錯誤處理增強**
   - 更新所有 services
   - Try-catch-finally 模式
   - 自動清理機制

2. **狀態一致性**
   - `get_project_by_id()` 增強
   - 同時查詢 DB 和 Docker 狀態
   - 狀態差異檢測和修復

3. **Rollback Mechanism**
   - Provision 失敗處理
   - Container cleanup
   - Error logging

4. **測試**
   - 失敗場景測試
   - Rollback 測試
   - 狀態一致性測試

### Phase 8: MVP-7 Demo Storyline (Task #8)

1. **整合測試腳本**
   - 建立 `tests/test_integration.py`
   - 完整流程測試

2. **Demo 腳本**
   - 建立 `scripts/demo.py`
   - 自動化 demo 流程

3. **文件完善**
   - 更新 README.md
   - API 使用範例
   - Troubleshooting guide

4. **最終驗證**
   - 完整流程測試
   - 效能測試
   - 錯誤處理測試

## Docker 基礎映像設計

### Base Image (docker/base-image/Dockerfile)

```dockerfile
FROM python:3.11-slim

# 安裝必要工具
RUN apt-get update && apt-get install -y \
    git \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# 建立工作目錄
RUN mkdir -p /workspace/repo

WORKDIR /workspace

# 保持容器運行
CMD ["tail", "-f", "/dev/null"]
```

## 開發環境設定

### docker-compose.yml

```yaml
version: '3.8'

services:
  mongodb:
    image: mongo:7
    container_name: refactor-mongodb
    ports:
      - "27017:27017"
    environment:
      MONGO_INITDB_DATABASE: refactor_db
    volumes:
      - mongodb_data:/data/db

  api:
    build:
      context: .
      dockerfile: docker/Dockerfile
    container_name: refactor-api
    ports:
      - "8000:8000"
    environment:
      - MONGODB_URL=mongodb://mongodb:27017
      - DATABASE_NAME=refactor_db
    volumes:
      - ./app:/app/app
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - mongodb

volumes:
  mongodb_data:
```

## 測試策略

### 單元測試
- 測試每個 service 方法
- Mock Docker 和 MongoDB 操作
- 測試錯誤處理

### 整合測試
- 測試完整 API 流程
- 使用 testcontainers 或 docker-compose
- 測試 SSE 串流

### E2E 測試
- 完整的 demo 流程
- 真實的 Docker 容器和 MongoDB

## 安全考量

1. **容器隔離**
   - 使用 Docker network 隔離
   - 限制容器權限
   - 資源限制 (CPU, Memory)

2. **輸入驗證**
   - 驗證 repo_url 格式
   - 驗證 command 內容
   - 防止 command injection

3. **認證授權**
   - API Key 機制 (後續階段)
   - Rate limiting

## 效能優化

1. **非同步操作**
   - 使用 async/await
   - 背景任務處理長時間操作

2. **連接池**
   - MongoDB 連接池
   - Docker client 重用

3. **快取**
   - 專案狀態快取
   - 容器資訊快取

## 監控和日誌

1. **應用日誌**
   - 結構化日誌
   - 不同 level (DEBUG, INFO, ERROR)

2. **指標收集**
   - API 請求統計
   - 容器資源使用

3. **健康檢查**
   - `/health` endpoint
   - MongoDB 連接檢查
   - Docker daemon 檢查

## 部署考量

1. **容器化部署**
   - 使用 Docker Compose 或 Kubernetes
   - 環境變數注入

2. **擴展性**
   - 支援多個 worker
   - 分散式任務處理 (未來)

3. **備份策略**
   - MongoDB 自動備份
   - 專案資料備份

## 時程規劃

- **Week 1**: Phase 1-2 (基礎架構 + MVP-1)
- **Week 2**: Phase 3-4 (MVP-2 + MVP-3)
- **Week 3**: Phase 5-6 (MVP-4 + MVP-5)
- **Week 4**: Phase 7-8 (MVP-6 + MVP-7 + 整合測試)

## 風險評估

1. **Docker 操作複雜度**
   - 風險：Docker SDK 使用複雜
   - 緩解：充分測試，參考官方文件

2. **SSE 連接穩定性**
   - 風險：長時間連接可能中斷
   - 緩解：實作 ping/pong 機制，重連邏輯

3. **容器資源管理**
   - 風險：容器洩漏或資源耗盡
   - 緩解：設定資源限制，定期清理

4. **Git Clone 失敗**
   - 風險：私有 repo、大型 repo
   - 緩解：支援 SSH key、超時設定、進度回饋

## 後續優化方向

1. **AI 整合**
   - 整合 LLM API 進行程式碼分析
   - 自動生成重構建議

2. **多語言支援**
   - 支援不同語言的基礎映像
   - 自動偵測專案類型

3. **協作功能**
   - 多用戶支援
   - 專案分享

4. **CI/CD 整合**
   - Webhook 支援
   - 自動化測試流程

## 參考資源

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker SDK for Python](https://docker-py.readthedocs.io/)
- [Motor (MongoDB Async Driver)](https://motor.readthedocs.io/)
- [SSE-Starlette](https://github.com/sysid/sse-starlette)

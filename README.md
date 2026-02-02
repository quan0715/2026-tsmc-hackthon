# AI 舊程式碼智能重構系統

這是一個前後端分離的大型專案,目標是建立一個智能程式碼重構系統。

## 功能特色

- ✅ 隔離的 Docker 容器環境
- ✅ RESTful API 管理專案生命週期
- ✅ 即時日誌串流 (SSE)
- ✅ Git repository 整合
- ✅ AI 重構邏輯僅在容器內的 `/agent` 模組執行，後端只負責觸發與監控

## 技術棧

- **後端**: FastAPI (Python 3.11+)
- **資料庫**: MongoDB 7
- **容器**: Docker & Docker Compose
- **其他**: Motor, SSE-Starlette, GitPython, Docker SDK

## 快速開始

### 前置需求

- Docker 和 Docker Compose
- Python 3.11+
- Git

### 安裝步驟

1. **Clone 專案**
   ```bash
   git clone <repo-url>
   cd auto-refactor-agent
   ```

2. **建立環境變數檔案**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **建立基礎容器映像（包含 Agent 程式碼）**
   ```bash
   # 重要：必須從專案根目錄執行，以便正確複製 agent/ 目錄
   docker build -t refactor-base:latest -f devops/base-image/Dockerfile .

   # 驗證 Agent 已包含在 image 中
   docker run --rm refactor-base:latest ls -la /workspace/agent/
   ```

4. **啟動服務**
   ```bash
   docker-compose -f devops/docker-compose.yml up -d
   ```

5. **查看 API 文件**
   ```bash
   open http://localhost:8000/docs
   ```

### 開發環境設置

```bash
# 建立虛擬環境
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
```

## API 端點

### 健康檢查
```bash
# 健康檢查
GET /api/v1/health
```

### 專案管理
```bash
# 建立專案
POST /api/v1/projects

# 查詢專案
GET /api/v1/projects/{id}

# 列出所有專案
GET /api/v1/projects

# Provision 專案
POST /api/v1/projects/{id}/provision

# 執行指令
POST /api/v1/projects/{id}/exec

# 串流日誌
GET /api/v1/projects/{id}/logs/stream

# 停止專案
POST /api/v1/projects/{id}/stop

# 刪除專案
DELETE /api/v1/projects/{id}
```

## 使用範例

### 快速 Demo

執行完整功能 Demo（自動化展示所有功能）:

```bash
cd backend
python3 scripts/demo.py
```

Demo 將展示：
1. 建立專案
2. Provision 容器並 clone repository
3. 查詢專案狀態（包含 Docker 狀態）
4. 即時串流日誌 (SSE)
5. 在容器中執行指令
6. 停止專案容器
7. 刪除專案和容器

### 完整工作流程

```bash
# 1. 建立專案
PROJECT_ID=$(curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/user/repo.git",
    "branch": "main",
    "init_prompt": "重構專案"
  }' | jq -r '.id')

# 2. Provision 專案 (建立容器並 clone repository)
curl -X POST http://localhost:8000/api/v1/projects/$PROJECT_ID/provision

# 3. 查詢專案狀態（包含 Docker 狀態一致性檢查）
curl "http://localhost:8000/api/v1/projects/$PROJECT_ID?include_docker_status=true"

# 4. 查看即時日誌
curl -N "http://localhost:8000/api/v1/projects/$PROJECT_ID/logs/stream?follow=true&tail=50"

# 5. 執行指令
curl -X POST http://localhost:8000/api/v1/projects/$PROJECT_ID/exec \
  -H "Content-Type: application/json" \
  -d '{
    "command": "ls -la",
    "workdir": "/workspace/repo"
  }'

# 6. 停止專案
curl -X POST http://localhost:8000/api/v1/projects/$PROJECT_ID/stop

# 7. 刪除專案（同時清理容器和資料庫）
curl -X DELETE http://localhost:8000/api/v1/projects/$PROJECT_ID
```

### API 詳細範例

#### 建立專案

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/octocat/Hello-World.git",
    "branch": "master",
    "init_prompt": "重構專案以提升可維護性"
  }'
```

回應：
```json
{
  "id": "697b96a683418e98d6dfa6f0",
  "repo_url": "https://github.com/octocat/Hello-World.git",
  "branch": "master",
  "init_prompt": "重構專案以提升可維護性",
  "status": "CREATED",
  "container_id": null,
  "created_at": "2026-01-29T17:00:00.000000",
  "updated_at": "2026-01-29T17:00:00.000000",
  "last_error": null,
  "docker_status": null
}
```

#### Provision 專案

```bash
curl -X POST http://localhost:8000/api/v1/projects/697b96a683418e98d6dfa6f0/provision
```

回應：
```json
{
  "message": "專案 provision 成功",
  "project_id": "697b96a683418e98d6dfa6f0",
  "container_id": "dfc5519659c9",
  "status": "READY"
}
```

#### 查詢專案狀態（含 Docker 狀態）

```bash
curl "http://localhost:8000/api/v1/projects/697b96a683418e98d6dfa6f0?include_docker_status=true"
```

回應：
```json
{
  "id": "697b96a683418e98d6dfa6f0",
  "status": "READY",
  "container_id": "dfc5519659c9",
  "docker_status": {
    "id": "dfc5519659c9",
    "name": "refactor-project-697b96a683418e98d6dfa6f0",
    "status": "running",
    "image": "refactor-base:latest"
  }
}
```

#### 執行指令

```bash
curl -X POST http://localhost:8000/api/v1/projects/697b96a683418e98d6dfa6f0/exec \
  -H "Content-Type: application/json" \
  -d '{
    "command": "git log --oneline -n 5",
    "workdir": "/workspace/repo"
  }'
```

回應：
```json
{
  "exit_code": 0,
  "stdout": "7fd1a60 Merge pull request #6\n...",
  "stderr": ""
}
```

#### SSE 日誌串流

```bash
# 不 follow (只取最後 10 行)
curl -N "http://localhost:8000/api/v1/projects/697b96a683418e98d6dfa6f0/logs/stream?follow=false&tail=10"

# Follow 模式 (持續串流)
curl -N "http://localhost:8000/api/v1/projects/697b96a683418e98d6dfa6f0/logs/stream?follow=true&tail=50"
```

SSE 事件格式：
```
data: {"line": "log content here", "number": 1}

event: ping
data: {"timestamp": 1234567890.123}

event: end
data: {"total_lines": 100}
```

## 專案結構

```
auto-refactor-agent/
├── backend/                    # 後端 FastAPI 應用
│   ├── app/
│   │   ├── main.py            # 應用入口
│   │   ├── config.py          # 配置管理
│   │   ├── models/            # 資料模型
│   │   ├── schemas/           # API Schema
│   │   ├── services/          # 業務邏輯
│   │   ├── routers/           # API 路由
│   │   └── database/          # 資料庫連接
│   ├── tests/                 # 測試
│   └── requirements.txt       # Python 依賴
├── devops/                     # DevOps 配置
│   ├── docker-compose.yml     # 開發環境
│   ├── api/Dockerfile         # API 服務
│   └── base-image/Dockerfile  # 基礎容器映像
├── agent/                      # 容器內執行的 AI Agent（唯一維護的 AI 邏輯）
└── frontend/                   # 前端 (未來實作)
```

## Docker 管理

```bash
# 查看服務狀態
docker-compose -f devops/docker-compose.yml ps

# 查看日誌
docker-compose -f devops/docker-compose.yml logs -f api

# 重啟服務
docker-compose -f devops/docker-compose.yml restart

# 停止服務
docker-compose -f devops/docker-compose.yml down

# 停止並清除資料
docker-compose -f devops/docker-compose.yml down -v
```

## 測試

```bash
# 執行測試
cd backend
pytest

# 執行特定測試
pytest tests/test_projects.py

# 執行測試並顯示覆蓋率
pytest --cov=app
```

## 功能特點

### 錯誤處理與回滾機制

系統具備完善的錯誤處理和自動回滾機制：

- **Provision 失敗回滾**: 如果 provision 過程中出現錯誤（如無效的 repo URL 或分支），系統會：
  - 自動清理已建立的容器
  - 將專案狀態更新為 `FAILED`
  - 記錄詳細的錯誤訊息到 `last_error` 欄位

- **狀態一致性檢查**: 查詢專案時可選擇包含 Docker 狀態檢查：
  - 即時查詢容器狀態（running, exited, not_found）
  - 自動偵測資料庫與 Docker 狀態不一致
  - 在日誌中記錄警告訊息

範例（Provision 失敗）:
```json
{
  "status": "FAILED",
  "last_error": "Clone repository 失敗: fatal: Remote branch xxx not found",
  "container_id": null,
  "docker_status": null
}
```

範例（狀態不一致）:
```json
{
  "status": "READY",
  "container_id": "abc123",
  "docker_status": {
    "status": "not_found",
    "inconsistent": true
  }
}
```

### SSE 日誌串流

支援 Server-Sent Events 即時日誌串流：

- **Follow 模式**: 持續串流新日誌（類似 `docker logs -f`）
- **Tail 限制**: 只取最後 N 行日誌
- **Keep-alive**: 每 30 秒發送 ping 事件保持連接
- **優雅關閉**: 自動清理 subprocess 資源

### 容器生命週期管理

完整的容器生命週期管理：

- **建立與啟動**: 自動配置網路、記憶體、CPU 限制
- **執行指令**: 支援自訂工作目錄和指令執行
- **停止**: 優雅停止容器（timeout 10 秒）
- **刪除**: 同時清理容器和資料庫記錄

## 故障排除

### MongoDB 連接失敗
```bash
# 確認 MongoDB 容器正在運行
docker ps | grep mongodb

# 檢查 MongoDB 日誌
docker logs refactor-mongodb
```

### API 服務無法啟動
```bash
# 檢查 API 日誌
docker logs refactor-api

# 確認環境變數設定
cat backend/.env
```

### 容器無法建立
```bash
# 確認 Docker 權限
docker ps

# 確認基礎映像存在
docker images | grep refactor-base

# 重新建立基礎映像
docker build -t refactor-base:latest -f devops/base-image/Dockerfile devops/base-image/
```

### Provision 失敗
```bash
# 查詢專案狀態和錯誤訊息
curl "http://localhost:8000/api/v1/projects/{project_id}"

# 檢查容器日誌（如果容器已建立）
docker logs refactor-project-{project_id}

# 常見原因：
# - 無效的 Git repository URL
# - 不存在的分支名稱
# - 網路連接問題
# - Git 認證失敗（私有 repo）
```

### 狀態不一致
```bash
# 如果 docker_status.inconsistent = true，表示：
# - 容器在 Docker 中不存在，但資料庫有記錄
# - 可能是容器被手動刪除

# 解決方式：刪除專案重新建立
curl -X DELETE "http://localhost:8000/api/v1/projects/{project_id}"
```

## 開發指南

### 新增 API 端點

1. 在 `backend/app/schemas/` 建立 Schema
2. 在 `backend/app/services/` 建立 Service
3. 在 `backend/app/routers/` 建立 Router
4. 在 `backend/app/main.py` 註冊 Router
5. 在 `backend/tests/` 建立測試

### 資料庫操作

使用 Motor (非同步 MongoDB driver):
```python
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends
from app.database.mongodb import get_database

async def my_function(db: AsyncIOMotorDatabase = Depends(get_database)):
    result = await db.collection_name.find_one({"_id": id})
    return result
```

## 授權

MIT License

## 聯絡方式

如有問題或建議,請開 issue。

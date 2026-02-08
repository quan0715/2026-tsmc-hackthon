# Chat Feature 測試指南

本指南說明如何測試新的聊天功能（支援多輪對話和持久化）。

## 前置需求

1. 確保已更新 `agent/requirements.txt` 中的依賴
2. 重建 base image 以包含新的 postgres 套件

## 快速開始

### 1. 重建 Base Image

```bash
# 從專案根目錄執行
docker build -t refactor-base:latest -f devops/base-image/Dockerfile .
```

### 2. 啟動所有服務

```bash
docker compose -f devops/docker-compose.yml up -d --build
```

這會啟動：
- MongoDB (port 27017)
- PostgreSQL (port 5432)
- API Server (port 8000)
- Frontend (port 5173)

### 3. 驗證 PostgreSQL

```bash
# 檢查 PostgreSQL 是否正常運行
docker compose -f devops/docker-compose.yml logs postgres

# 連接到 PostgreSQL
docker exec -it refactor-postgres psql -U langgraph -d langgraph
```

## 測試流程

### 方式 1: 透過前端 UI

1. 打開 http://localhost:5173
2. 登入或註冊帳號
3. 點擊「建立新專案」
4. 選擇「沙盒測試」類型
5. 輸入初始訊息（例如：「列出當前目錄的檔案」）
6. 建立專案後會自動導向聊天頁面
7. 測試多輪對話：
   - 發送第一則訊息
   - 等待 AI 回應
   - 發送後續訊息
   - 驗證 AI 能記住之前的對話內容

### 方式 2: 透過 API

```bash
# 1. 登入獲取 token
TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}' | jq -r '.access_token')

# 2. 建立 Sandbox 專案
PROJECT_ID=$(curl -s -X POST "http://localhost:8000/api/v1/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "project_type": "SANDBOX",
    "spec": "Hello, list the files in the current directory"
  }' | jq -r '.id')

echo "Project ID: $PROJECT_ID"

# 3. Provision 專案
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/provision" \
  -H "Authorization: Bearer $TOKEN"

# 4. 發送聊天訊息
CHAT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello! Please list the files in /workspace"}')

echo $CHAT_RESPONSE
TASK_ID=$(echo $CHAT_RESPONSE | jq -r '.task_id')
THREAD_ID=$(echo $CHAT_RESPONSE | jq -r '.thread_id')

# 5. 串流接收回應
curl -N "http://localhost:8000/api/v1/projects/$PROJECT_ID/chat/$TASK_ID/stream" \
  -H "Authorization: Bearer $TOKEN"

# 6. 發送第二則訊息（同一 thread）
curl -s -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Now create a file called hello.txt\", \"thread_id\": \"$THREAD_ID\"}"
```

## 驗證持久化

### 檢查 PostgreSQL 中的資料

```bash
docker exec -it refactor-postgres psql -U langgraph -d langgraph

# 在 psql 中執行
\dt  -- 列出所有表

# 查看 checkpoints（對話狀態）
SELECT thread_id, checkpoint_id, created_at FROM checkpoints ORDER BY created_at DESC LIMIT 10;
```

### 驗證重啟後對話恢復

1. 在聊天中進行幾輪對話
2. 記下 thread_id
3. 重啟服務：`docker compose -f devops/docker-compose.yml restart`
4. 使用相同的 thread_id 繼續對話
5. 驗證 AI 能記住之前的上下文

## 預期行為

### Sandbox 專案
- 不需要 repo_url
- Provision 時會建立空的工作空間（包含 memory/AGENTS.md）
- 可以進行多輪對話
- 對話歷史透過 PostgreSQL 持久化

### 重構專案（原有功能）
- 需要 repo_url
- Provision 時會 clone repository
- 保持原有的重構流程

## 常見問題

### PostgreSQL 連線失敗

確認容器網路設定正確：
```bash
docker network inspect refactor-network
```

容器內應該能透過 `postgres:5432` 連接到 PostgreSQL。

### Agent 無法持久化

檢查 POSTGRES_URL 環境變數是否正確傳遞：
```bash
# 檢查 API 容器的環境變數
docker exec refactor-api env | grep POSTGRES

# 檢查專案容器的環境變數
docker exec refactor-project-<project_id> env | grep POSTGRES
```

### 對話沒有保存

1. 確認使用了正確的 thread_id
2. 檢查 PostgreSQL 日誌：`docker compose -f devops/docker-compose.yml logs postgres`
3. 確認 `langgraph-checkpoint-postgres` 套件已安裝

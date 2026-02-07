# Reforge

AI Refactoring. Measured. Continuous.

基於 LangChain Deep Agents 的智能程式碼分析與重構服務，提供隔離的 Docker 容器環境進行安全的程式碼重構。

## 快速開始

### 前置需求

- Docker & Docker Compose
- Git
- (開發環境) Python 3.11+, Node.js 18+

### 環境設定

1. **設定 Backend 環境變數**

```bash
cd backend
cp .env.example .env
# 編輯 .env，填入必要的配置（特別是 ANTHROPIC_API_KEY）
```

必要配置項：
- `JWT_SECRET_KEY` - JWT 簽名金鑰（生產環境務必更換）
- `MONGODB_URL` - MongoDB 連接字串
- `DOCKER_BASE_IMAGE` - Base Docker Image 名稱
- `DOCKER_NETWORK` - Docker 網路名稱

**注意**: LLM API Key（如 `ANTHROPIC_API_KEY`）由容器內的 AI Server 自行管理，不需要在後端 `.env` 中設定

2. **建立 Base Image**

```bash
# 從專案根目錄執行
docker build -t refactor-base:latest -f devops/base-image/Dockerfile .
```

Dockerfile 位置：
- Backend：`backend/Dockerfile`（開發）、`backend/Dockerfile.prod`（正式）
- Frontend：`frontend/Dockerfile`（開發）、`frontend/Dockerfile.prod`（正式）

### 啟動服務

**Docker Compose（開發/測試）**

```bash
# 啟動所有服務（PostgreSQL + MongoDB + Backend API + Frontend）
docker-compose -f devops/docker-compose.yml up -d

# 查看服務狀態
docker-compose -f devops/docker-compose.yml ps

# 查看日誌
docker-compose -f devops/docker-compose.yml logs -f api

# 停止服務
docker-compose -f devops/docker-compose.yml down
```

**GCE 單機（正式環境）**

- 使用 `devops/docker-compose.prod.yml`
- 設定 `REGISTRY_HOST` / `GCP_PROJECT_ID` / `GAR_REPOSITORY` / `IMAGE_TAG`
- 映像從 Artifact Registry 拉取

服務端點：
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

**本地開發模式**

```bash
# 1. 啟動 MongoDB
docker run -d --name mongodb -p 27017:27017 mongo:7

# 2. 啟動 Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 3. 啟動 Frontend
cd frontend
npm install
npm run dev  # 開啟 http://localhost:5173
```

## 使用方式

### 1. 註冊/登入

```bash
# 註冊新使用者
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"testuser","password":"password123"}'

# 登入
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'
```

### 2. 建立專案

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/yourusername/your-repo.git",
    "branch": "main",
    "init_prompt": "分析此專案並生成重構計劃"
  }'
```

### 3. Provision 專案

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/provision \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. 執行 AI Agent

```bash
# 啟動 Agent 分析
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/agent/run \
  -H "Authorization: Bearer YOUR_TOKEN"

# 查詢任務狀態
curl http://localhost:8000/api/v1/projects/{project_id}/agent/runs/{run_id} \
  -H "Authorization: Bearer YOUR_TOKEN"

# SSE 串流執行日誌
curl -N http://localhost:8000/api/v1/projects/{project_id}/agent/runs/{run_id}/stream \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 測試

```bash
# 執行完整 E2E 測試
./test_cloud_run_e2e_v2.sh

# 測試 base image 建置
export ANTHROPIC_API_KEY=your-api-key
./test_base_image.sh
```

## 系統架構

```
┌─────────────┐      HTTP      ┌──────────────────┐
│   Frontend  │ <────────────> │   Backend API    │
│ (React/Vite)│                │    (FastAPI)     │
└─────────────┘                └────────┬─────────┘
                                        │
                       ┌────────────────┼────────────────┐
                       │                │                │
                       v                v                v
                 ┌──────────┐   ┌──────────────┐  ┌──────────┐
                 │ MongoDB  │   │Docker Network│  │ Project  │
                 │          │   │              │  │Container │
                 └──────────┘   └──────┬───────┘  └────┬─────┘
                                       │               │
                                       │    HTTP       │
                                       └───────────────┤
                                                       │
                                                 ┌─────v──────┐
                                                 │ AI Server  │
                                                 │  (FastAPI) │
                                                 │            │
                                                 │ Deep Agent │
                                                 └────────────┘
```

## 技術棧

- **Backend**: FastAPI, Python 3.11, MongoDB, PostgreSQL
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui
- **AI/ML**: LangChain, Deep Agents, Anthropic Claude
- **容器**: Docker, Docker Compose
- **認證**: JWT (JSON Web Tokens)

## 文件

- **[docs/API.md](./docs/API.md)** - REST API 完整規格
- **[docs/BACKEND.md](./docs/BACKEND.md)** - 後端技術文件
- **[docs/guides/](./docs/guides/)** - 使用指南
- **[docs/testing/](./docs/testing/)** - 測試文件
- **[CLAUDE.md](./CLAUDE.md)** - Claude Code 專案指引

## 常見問題

### 容器無法啟動？

確認 base image 已正確建立：
```bash
docker images | grep refactor-base
```

### Agent 執行失敗？

1. 檢查容器內 AI Server 的 LLM API Key 設定
2. 查看容器日誌：`docker logs refactor-project-{project_id}`
3. 檢查 API 日誌：`docker-compose -f devops/docker-compose.yml logs -f api`

### 如何清理測試資料？

```bash
# 停止並移除所有容器和資料
docker-compose -f devops/docker-compose.yml down -v

# 清理專案容器
docker ps -a | grep refactor-project | awk '{print $1}' | xargs docker rm -f
```

## License

MIT

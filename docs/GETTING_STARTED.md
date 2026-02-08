# Getting Started

本文檔提供本專案最常見的兩種啟動方式：

1. Docker Compose (推薦): 一次啟動資料庫 + API + 前端
2. 本地開發: DB 用 Docker 跑，API/Frontend 在本機跑

## 前置需求

- Docker Desktop (或 Docker Engine) + Docker Compose v2 (`docker compose`)
- Git
- (本地開發) Python 3.11+、Node.js 20+

## 方式 A: Docker Compose (推薦)

### 1) 建立 `backend/.env`

```bash
cp backend/.env.example backend/.env
```

至少請確認以下變數已設定為正確值：

- `POSTGRES_URL`
- `MONGODB_URL`
- `JWT_SECRET_KEY` (生產環境務必替換)
- `ANTHROPIC_API_KEY` (若要使用 Anthropic/Claude)

注意：`ANTHROPIC_API_KEY` 由 Backend 讀取後，會注入到每個專案的「Project Container」中使用；未設定時，專案容器將無法使用 Anthropic 模型。

### 2) 建置 Project Base Image (必須)

專案會為每個 Project 建立隔離容器，這些容器使用 base image `refactor-base:latest`。

```bash
docker build -t refactor-base:latest -f devops/base-image/Dockerfile .
```

### 3) 啟動服務

```bash
docker compose -f devops/docker-compose.yml up -d --build
docker compose -f devops/docker-compose.yml ps
```

服務端點：

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- Swagger/OpenAPI: `http://localhost:8000/docs`

### 4) 停止與清理

```bash
docker compose -f devops/docker-compose.yml down
```

若要連資料一起清：

```bash
docker compose -f devops/docker-compose.yml down -v
```

## 方式 B: 本地開發 (API/Frontend 在本機跑)

### 1) 先啟動資料庫 (Docker)

```bash
docker compose -f devops/docker-compose.yml up -d postgres mongodb
```

### 2) 啟動 Backend (本機)

```bash
python -m venv backend/.venv
source backend/.venv/bin/activate
pip install -r backend/requirements.txt

export MONGODB_URL="mongodb://localhost:27017"
export MONGODB_DATABASE="refactor_agent"
export POSTGRES_URL="postgresql://langgraph:langgraph_secret@localhost:5432/langgraph"
export JWT_SECRET_KEY="dev-secret-key"
export ANTHROPIC_API_KEY="your-api-key"

cd backend
uvicorn app.main:app --reload --port 8000
```

### 3) 啟動 Frontend (本機)

```bash
cd frontend
npm ci
npm run dev
```

## 下一步

- 使用流程請看 `docs/USAGE.md`
- 環境變數請看 `docs/CONFIGURATION.md`
- 部署請看 `docs/DEPLOYMENT.md`

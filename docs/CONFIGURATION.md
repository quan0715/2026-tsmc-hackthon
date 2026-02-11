# Configuration

本專案主要透過 `backend/.env` 控制行為。請以 `backend/.env.example` 為來源，將必要值填入 `backend/.env`。

## 必填 (核心功能)

### MongoDB

- `MONGODB_URL`: MongoDB 連線字串
- `MONGODB_DATABASE`: DB 名稱

Docker Compose 開發環境預設為：

- `MONGODB_URL=mongodb://mongodb:27017`
- `MONGODB_DATABASE=refactor_agent`

本機執行 Backend 時常用：

- `MONGODB_URL=mongodb://localhost:27017`

### PostgreSQL (必填)

- `POSTGRES_URL`: Agent/LangGraph 會話持久化用資料庫

Docker Compose 開發環境預設為：

- `POSTGRES_URL=postgresql://langgraph:langgraph_secret@postgres:5432/langgraph`

本機執行 Backend 時常用：

- `POSTGRES_URL=postgresql://langgraph:langgraph_secret@localhost:5432/langgraph`

### JWT

- `JWT_SECRET_KEY`: JWT 簽名密鑰 (生產環境務必替換為安全隨機值)
- `JWT_ALGORITHM`: 預設 `HS256`
- `JWT_ACCESS_TOKEN_EXPIRE_HOURS`: token 有效期 (小時)

### LLM (Anthropic/Claude)

- `ANTHROPIC_API_KEY`: 會由 Backend 注入到專案容器 (Project Container) 中使用

若未設定，Backend 仍可啟動，但專案容器無法使用 Anthropic 模型，且你會在後端日誌看到警告。

## Docker/容器相關

### Base image

- `DOCKER_BASE_IMAGE`: 預設 `refactor-base:latest`

此 image 用來建立每個 Project 的隔離容器，請先建置：

```bash
docker build -t refactor-base:latest -f devops/base-image/Dockerfile .
```

### Network / Volumes

- `DOCKER_NETWORK`: 預設 `refactor-network`
- `DOCKER_VOLUME_PREFIX`: 預設 `/tmp/refactor-workspaces`

Backend 會在 `${DOCKER_VOLUME_PREFIX}/${project_id}/` 建立工作目錄，並掛載到專案容器：

- `/workspace/repo`
- `/workspace/artifacts`

## 可選: Vertex AI

若要在專案容器使用 Vertex AI 相關模型：

- `GCP_PROJECT_ID`
- `GCP_LOCATION` (例如 `us-central1`)
- `GOOGLE_APPLICATION_CREDENTIALS` (選填)

行為概要：

- 若設定 `GOOGLE_APPLICATION_CREDENTIALS` 且檔案存在，Backend 會將其複製到 workspace volume 並掛載進專案容器。
- 否則 Backend 會嘗試使用 API 容器中的 ADC 檔案 (`/root/.config/gcloud/application_default_credentials.json`)。

細節請看 `docs/VERTEX_AI.md`。

## 可選: 容器資源限制

- `CONTAINER_CPU_LIMIT` (例如 `4.0`)
- `CONTAINER_MEMORY_LIMIT` (例如 `8g`)

## 可選: Git

- `GIT_CLONE_TIMEOUT`
- `GIT_DEPTH`

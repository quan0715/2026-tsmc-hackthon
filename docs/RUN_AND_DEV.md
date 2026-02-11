# Run And Dev

本文整理常用的啟動、檢查、以及開發時需要知道的操作點。

## 常用腳本

### 開發環境一鍵啟動

```bash
./scripts/deploy-dev.sh
```

需求：

- Docker daemon 可用
- `backend/.env` 已存在 (可由 `backend/.env.example` 複製)

### 環境健檢

```bash
./scripts/check-env.sh
```

此腳本會檢查：

- Docker daemon
- `refactor-base:latest` 是否存在
- `refactor-network` 是否存在
- MongoDB/API/Frontend 是否可連
- `backend/.env` 是否有必要變數

## Base Image (Project Container)

每個 Project 都會建立隔離的 Docker container，使用 `DOCKER_BASE_IMAGE` (預設 `refactor-base:latest`)。

當你更新 `agent/` 或 `devops/base-image/Dockerfile` 時，通常需要重新建置 base image：

```bash
docker build -t refactor-base:latest -f devops/base-image/Dockerfile .
```

## 工作目錄與檔案掛載

Backend 會在 `${DOCKER_VOLUME_PREFIX}/${project_id}/` 建立資料夾，並掛載到專案容器：

- `${...}/${project_id}/repo` -> `/workspace/repo`
- `${...}/${project_id}/artifacts` -> `/workspace/artifacts`

開發用 docker compose 預設把 host 的 `/tmp/refactor-workspaces` 掛到 API 容器，並由 API 再建立專案 workspace。

## 本機開發建議

1. DB 用 Compose 跑：`docker compose -f devops/docker-compose.yml up -d postgres mongodb`
2. Backend/Frontend 用本機跑：可快速迭代、也較好除錯

詳細流程可回看 `docs/GETTING_STARTED.md`。

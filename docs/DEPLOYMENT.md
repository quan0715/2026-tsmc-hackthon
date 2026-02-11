# Deployment

本專案的生產環境通常是：

- GitHub Actions: 建置並推送 images 到 Google Artifact Registry (GAR)
- GCE: 使用 `devops/docker-compose.prod.yml` 以 image tag 拉取並啟動

細節流程與 GitHub 設定請看：

- `.github/workflows/README.md`
- `.github/workflows/GCE_DEPLOY.md`

## Production Compose 概念

`devops/docker-compose.prod.yml` 會啟動：

- `postgres` (5432)
- `mongodb` (27017)
- `api` (host 8000 -> container 8000)
- `frontend` (host 80 -> container 80, Nginx 反向代理 `/api` 到 `api:8000`)

因此常見對外入口是：

- `http://YOUR_HOST/` (Frontend)
- `http://YOUR_HOST/api/v1/...` (透過 Nginx 反向代理到 API)

同時 API 也會直接暴露 `http://YOUR_HOST:8000` (如不希望對外開放，可再調整 compose)。

## 在主機上手動啟用 (不透過 GitHub Actions)

適合：你已經手動把 image 推到 GAR，想在主機上拉取並啟動。

### 1) 準備 `backend/.env`

在主機的 repo 目錄中建立 `backend/.env` (可由 `backend/.env.example` 複製)，至少要有：

- `POSTGRES_URL` (在 compose 中通常用 `postgres` hostname)
- `MONGODB_URL` (在 compose 中通常用 `mongodb` hostname)
- `JWT_SECRET_KEY`
- `ANTHROPIC_API_KEY` (如需 Anthropic)

### 2) 設定必要環境變數

`devops/docker-compose.prod.yml` 需要這些變數才能組成 image name：

```bash
export REGISTRY_HOST="us-central1-docker.pkg.dev"
export GCP_PROJECT_ID="your-project-id"
export GAR_REPOSITORY="images"
export IMAGE_TAG="latest"   # 或使用 Git SHA 短碼，例如 abc1234
```

可選：

```bash
export WORKSPACE_HOST_DIR="/var/lib/refactor-workspaces"
```

### 3) 執行部署腳本

```bash
./scripts/deploy-prod.sh
```

此腳本會：

- 拉取 base image 並標記為 `refactor-base:latest` (供 Project Container 使用)
- `docker compose pull` 拉取 `api` 與 `frontend` images
- `docker compose up -d` 啟動 prod stack

## 防火牆與連線

最少需要對外開放：

- TCP 80 (Frontend)

如要直接對外打 API (非必要)：

- TCP 8000

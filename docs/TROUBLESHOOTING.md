# Troubleshooting

## Provision 失敗 / Agent 無法執行

常見原因：

- `POSTGRES_URL` 沒有設定或連不到 (Backend 會在建立 Project Container 時直接拒絕)
- `refactor-base:latest` 不存在
- `refactor-network` 不存在或 Backend 容器不在該 network

建議先跑：

```bash
./scripts/check-env.sh
```

## Base image 不存在

```bash
docker build -t refactor-base:latest -f devops/base-image/Dockerfile .
```

## Docker network 不存在

開發環境用 compose 啟動會自動建立：

```bash
docker compose -f devops/docker-compose.yml up -d
```

若你不是用 compose，手動建立：

```bash
docker network create refactor-network
```

## API health check 不通

```bash
curl -v http://localhost:8000/api/v1/health
docker logs refactor-api
```

## 前端打不到 API

開發環境前端預設直接打 `http://localhost:8000` (由 `devops/docker-compose.yml` 設定 `VITE_API_BASE_URL`)。

生產環境前端會走 Nginx 反向代理：

- `http://YOUR_HOST/api/...` -> `api:8000` (見 `devops/frontend/nginx.conf`)

## Vertex AI 相關錯誤

先確認 API 容器內是否存在 credentials：

- `/root/.config/gcloud/application_default_credentials.json` (ADC)
- 或 `GOOGLE_APPLICATION_CREDENTIALS` 指向的檔案

細節請看 `docs/VERTEX_AI.md`。

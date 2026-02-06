# GCE 部署設定指南

本文檔說明如何設定 GitHub Actions 自動部署到 Google Compute Engine (GCE)。

---

## 部署流程概覽

```
Push to main → CI/CD Pipeline → Build & Push Images → Deploy to GCE
     ↓              ↓                    ↓                    ↓
   測試通過      建置映像           推送到 GAR          更新 GCE 服務
```

---

## 必要的 GCP 資源

### 1. Service Account

建立一個 Service Account 並授予以下權限：

```bash
# 建立 Service Account
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer"

# 授予權限
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/compute.instanceAdmin.v1"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# 生成 JSON Key
gcloud iam service-accounts keys create github-deployer-key.json \
  --iam-account=github-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### 2. Artifact Registry

建立 Docker Repository：

```bash
gcloud artifacts repositories create images \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker images for auto-refactor-agent"
```

### 3. GCE Instance

建立 GCE 實例（或使用現有的）：

```bash
# 建立 Production 實例
gcloud compute instances create refactor-agent-prod \
  --zone=us-central1-a \
  --machine-type=n1-standard-2 \
  --image-family=cos-stable \
  --image-project=cos-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-standard \
  --tags=http-server,https-server

# 建立 Staging 實例（可選）
gcloud compute instances create refactor-agent-staging \
  --zone=us-central1-a \
  --machine-type=n1-standard-1 \
  --image-family=cos-stable \
  --image-project=cos-cloud \
  --boot-disk-size=30GB \
  --boot-disk-type=pd-standard \
  --tags=http-server,https-server
```

### 4. 防火牆規則

開放必要的端口：

```bash
# 允許 HTTP
gcloud compute firewall-rules create allow-http \
  --allow=tcp:80 \
  --target-tags=http-server

# 允許 HTTPS
gcloud compute firewall-rules create allow-https \
  --allow=tcp:443 \
  --target-tags=https-server

# 允許 API (8000)
gcloud compute firewall-rules create allow-api \
  --allow=tcp:8000 \
  --target-tags=http-server
```

---

## GitHub Repository 設定

### Repository Secrets

在 `Settings > Secrets and variables > Actions > Secrets` 中新增：

| Secret 名稱 | 說明 | 如何取得 |
|-----------|------|---------|
| **GCP_SA_KEY** | Service Account JSON Key | 從上面的步驟 1 取得 `github-deployer-key.json` 的完整內容 |

**重要**: 複製整個 JSON 檔案內容，包含開頭的 `{` 和結尾的 `}`

```bash
# 顯示 JSON key 內容（複製整個輸出）
cat github-deployer-key.json
```

### Repository Variables

在 `Settings > Secrets and variables > Actions > Variables` 中新增：

| 變數名稱 | 說明 | 範例值 |
|---------|------|--------|
| **REGISTRY_HOST** | GAR 主機名稱 | `us-central1-docker.pkg.dev` |
| **GCP_PROJECT_ID** | GCP 專案 ID | `your-project-id` |
| **GAR_REPOSITORY** | GAR Repository 名稱 | `images` |
| **GCE_INSTANCE_PROD** | Production GCE 實例名稱 | `refactor-agent-prod` |
| **GCE_ZONE_PROD** | Production GCE 區域 | `us-central1-a` |
| **GCE_INSTANCE_STAGING** | Staging GCE 實例名稱（可選） | `refactor-agent-staging` |
| **GCE_ZONE_STAGING** | Staging GCE 區域（可選） | `us-central1-a` |
| **VITE_API_BASE_URL** | Frontend API URL | `http://your-instance-ip:8000` |

---

## GCE Instance 初始化

SSH 到 GCE 實例並執行以下步驟：

### 1. 安裝 Docker 和 Docker Compose

```bash
# SSH 到實例
gcloud compute ssh refactor-agent-prod --zone=us-central1-a

# 安裝 Docker (Container-Optimized OS 已預裝)
# 如果是 Ubuntu/Debian，執行：
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# 將當前使用者加入 docker group
sudo usermod -aG docker $USER
```

### 2. 設定 gcloud 認證

```bash
# 在 GCE 實例上設定 gcloud
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
```

### 3. 部署專案檔案

```bash
# Clone 專案（或使用其他方式上傳 docker-compose.prod.yml）
cd ~
git clone https://github.com/YOUR_USERNAME/auto-refactor-agent.git
cd auto-refactor-agent

# 建立環境變數檔案
cat > .env.prod << 'EOF'
# MongoDB
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DATABASE=refactor_agent

# PostgreSQL
POSTGRES_URL=postgresql://langgraph:langgraph_secret@postgres:5432/langgraph

# JWT
JWT_SECRET_KEY=YOUR_PRODUCTION_SECRET_KEY_HERE
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24

# Anthropic API
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY_HERE

# Docker
DOCKER_BASE_IMAGE=refactor-base:latest
DOCKER_NETWORK=refactor-network
DOCKER_VOLUME_PREFIX=/var/refactor-workspaces

# Container resources
CONTAINER_CPU_LIMIT=2.0
CONTAINER_MEMORY_LIMIT=2g

# Git
GIT_CLONE_TIMEOUT=300
GIT_DEPTH=1

# Log
LOG_LEVEL=INFO
EOF

# 設定權限
chmod 600 .env.prod
```

### 4. 建立 Docker 網路

```bash
docker network create refactor-network
```

### 5. 測試部署

```bash
# 手動拉取映像測試
gcloud auth configure-docker us-central1-docker.pkg.dev
docker pull us-central1-docker.pkg.dev/YOUR_PROJECT_ID/images/refactor-base:latest

# 啟動服務
docker-compose -f devops/docker-compose.prod.yml up -d

# 檢查狀態
docker-compose -f devops/docker-compose.prod.yml ps

# 查看日誌
docker-compose -f devops/docker-compose.prod.yml logs -f
```

---

## 觸發部署

### 自動部署（Push to main）

當你 push 程式碼到 main 分支時：

```bash
git push origin main
```

部署流程會自動執行：
1. ✅ CI 測試
2. ✅ 建置並推送映像到 GAR
3. ✅ 自動部署到 GCE Production 環境

### 手動部署

透過 GitHub UI 手動觸發：

1. 前往 `Actions > Deploy to GCE`
2. 點擊 `Run workflow`
3. 選擇環境（production 或 staging）
4. 點擊 `Run workflow`

或使用 GitHub CLI：

```bash
# 部署到 Production
gh workflow run deploy-gce.yml -f environment=production

# 部署到 Staging
gh workflow run deploy-gce.yml -f environment=staging
```

---

## 驗證部署

### 檢查服務狀態

```bash
# SSH 到實例
gcloud compute ssh refactor-agent-prod --zone=us-central1-a

# 檢查容器狀態
docker ps

# 檢查日誌
docker logs refactor-api
docker logs refactor-frontend
```

### 測試 API

```bash
# 取得外部 IP
EXTERNAL_IP=$(gcloud compute instances describe refactor-agent-prod \
  --zone=us-central1-a \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

# 測試 API health endpoint
curl http://$EXTERNAL_IP:8000/health

# 測試 Frontend
curl http://$EXTERNAL_IP:80
```

---

## 故障排除

### 部署失敗

**檢查 GitHub Actions 日誌**：
- 前往 `Actions` 頁面
- 點擊失敗的 workflow run
- 查看詳細錯誤訊息

**常見問題**：

1. **Service Account 權限不足**
   ```bash
   # 檢查 Service Account 權限
   gcloud projects get-iam-policy YOUR_PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:serviceAccount:github-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com"
   ```

2. **GCE SSH 連接失敗**
   ```bash
   # 測試 SSH 連接
   gcloud compute ssh refactor-agent-prod --zone=us-central1-a --dry-run
   ```

3. **Docker 映像拉取失敗**
   ```bash
   # 在 GCE 上測試認證
   gcloud auth configure-docker us-central1-docker.pkg.dev
   docker pull us-central1-docker.pkg.dev/YOUR_PROJECT_ID/images/refactor-base:latest
   ```

### 健康檢查失敗

**檢查服務日誌**：

```bash
# SSH 到 GCE
gcloud compute ssh refactor-agent-prod --zone=us-central1-a

# 檢查容器狀態
docker ps -a

# 檢查 API 日誌
docker logs refactor-api --tail 100

# 檢查 Frontend 日誌
docker logs refactor-frontend --tail 100
```

**檢查防火牆規則**：

```bash
# 列出防火牆規則
gcloud compute firewall-rules list

# 測試端口連接
telnet YOUR_INSTANCE_IP 8000
```

---

## 回滾部署

如果新版本有問題，可以手動回滾到舊版本：

```bash
# SSH 到 GCE
gcloud compute ssh refactor-agent-prod --zone=us-central1-a

# 切換到專案目錄
cd ~/auto-refactor-agent

# 拉取舊版本映像（使用舊的 commit SHA）
OLD_TAG="abc1234"  # 替換為舊的 commit SHA (前 7 位)
docker pull us-central1-docker.pkg.dev/YOUR_PROJECT_ID/images/refactor-base:$OLD_TAG
docker pull us-central1-docker.pkg.dev/YOUR_PROJECT_ID/images/refactor-api:$OLD_TAG
docker pull us-central1-docker.pkg.dev/YOUR_PROJECT_ID/images/refactor-frontend:$OLD_TAG

# Tag 為 latest
docker tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/images/refactor-base:$OLD_TAG refactor-base:latest
docker tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/images/refactor-api:$OLD_TAG refactor-api:latest
docker tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/images/refactor-frontend:$OLD_TAG refactor-frontend:latest

# 重啟服務
docker-compose -f devops/docker-compose.prod.yml down
docker-compose -f devops/docker-compose.prod.yml up -d
```

---

## 安全建議

### 1. 限制 Service Account 權限

只授予必要的最小權限，不要使用 Owner 或 Editor 角色。

### 2. 使用私有 IP

考慮使用 Cloud NAT 和私有 IP，限制外部訪問：

```bash
gcloud compute instances create refactor-agent-prod \
  --no-address \
  --subnet=default \
  ...
```

### 3. 啟用 HTTPS

使用 Let's Encrypt 或 Google-managed SSL certificates。

### 4. 定期更新

- 定期更新 GCE 實例的作業系統
- 定期更新 Docker 映像的基礎映像
- 定期輪換 Service Account keys

---

## 監控與日誌

### Cloud Logging

```bash
# 查看 GCE 實例日誌
gcloud logging read "resource.type=gce_instance AND resource.labels.instance_id=YOUR_INSTANCE_ID" \
  --limit 50 \
  --format json
```

### Cloud Monitoring

設定告警：
- CPU 使用率 > 80%
- 記憶體使用率 > 80%
- 磁碟使用率 > 90%
- HTTP 5xx 錯誤率 > 1%

---

## 相關文檔

- [GitHub Actions CI/CD Pipeline](.github/workflows/README.md)
- [Docker Compose 配置](../../devops/docker-compose.prod.yml)
- [Backend 環境變數](../../backend/.env.example)

---

**最後更新**: 2026-02-06
**維護者**: Development Team

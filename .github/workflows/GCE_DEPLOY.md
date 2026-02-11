# GCE 部署完整指南

本文檔說明如何設定 GitHub Actions 自動部署到 Google Compute Engine (GCE)。

---

## 📋 部署流程概覽

```
Push to main → CI 測試 → Build 映像 → Push to GAR → 自動部署到 GCE
     ↓           ↓            ↓              ↓              ↓
  程式碼變更    測試通過     建置成功      推送成功      服務更新
```

**觸發方式**：
- ✅ 自動：Push to main 後自動部署
- ✅ 手動：透過 GitHub Actions UI 觸發

---

## 🔑 必要的 GitHub 設定

### Repository Secrets（機密資訊）

前往：`Settings > Secrets and variables > Actions > Secrets`

| Secret 名稱 | 說明 | 必填 |
|-----------|------|------|
| **GCP_SA_KEY** | GCP Service Account JSON Key | ✅ |
| **ANTHROPIC_API_KEY** | Anthropic API Key (Claude 模型) | ✅ |
| **JWT_SECRET_KEY** | JWT 加密密鑰 (可選，自動生成) | ❌ |

### Repository Variables（公開變數）

前往：`Settings > Secrets and variables > Actions > Variables`

| 變數名稱 | 說明 | 範例值 | 必填 |
|---------|------|--------|------|
| **REGISTRY_HOST** | Google Artifact Registry 主機 | `us-central1-docker.pkg.dev` | ✅ |
| **GCP_PROJECT_ID** | GCP 專案 ID | `your-project-id` | ✅ |
| **GAR_REPOSITORY** | GAR Repository 名稱 | `images` | ✅ |
| **GCE_INSTANCE** | GCE 實例名稱 | `refactor-agent-prod` | ✅ |
| **GCE_ZONE** | GCE 區域 | `us-central1-a` | ✅ |
| **VITE_API_BASE_URL** | Frontend API URL | `http://your-ip:8000` | ✅ |

---

## 🚀 快速設定步驟

### Step 1: 建立 Service Account

```bash
# 設定你的專案 ID
export PROJECT_ID="your-project-id"

# 建立 Service Account
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer" \
  --project=$PROJECT_ID

# 授予必要權限
for role in "roles/artifactregistry.writer" \
            "roles/compute.instanceAdmin.v1" \
            "roles/iam.serviceAccountUser"; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="$role"
done

# 生成 JSON Key
gcloud iam service-accounts keys create github-deployer-key.json \
  --iam-account=github-deployer@${PROJECT_ID}.iam.gserviceaccount.com

# 顯示 Key 內容（複製整個輸出到 GitHub Secrets）
cat github-deployer-key.json
```

**重要**：複製整個 JSON 內容（包含 `{` 和 `}`），貼到 GitHub Repository 的 **GCP_SA_KEY** secret。

### Step 2: 建立 GCP 資源

#### 2.1 建立 Artifact Registry

```bash
gcloud artifacts repositories create images \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker images for auto-refactor-agent" \
  --project=$PROJECT_ID
```

#### 2.2 建立 GCE 實例

```bash
gcloud compute instances create refactor-agent-prod \
  --zone=us-central1-a \
  --machine-type=n1-standard-2 \
  --image-family=cos-stable \
  --image-project=cos-cloud \
  --boot-disk-size=50GB \
  --boot-disk-type=pd-standard \
  --tags=http-server,https-server \
  --project=$PROJECT_ID
```

#### 2.3 設定防火牆規則

```bash
# 允許 HTTP (80)
gcloud compute firewall-rules create allow-http \
  --allow=tcp:80 \
  --target-tags=http-server \
  --project=$PROJECT_ID

# 允許 HTTPS (443)
gcloud compute firewall-rules create allow-https \
  --allow=tcp:443 \
  --target-tags=https-server \
  --project=$PROJECT_ID

# 允許 API (8000)
gcloud compute firewall-rules create allow-api \
  --allow=tcp:8000 \
  --target-tags=http-server \
  --project=$PROJECT_ID
```

### Step 3: 設定 GitHub Secrets & Variables

#### 設定 Secret

```bash
# 使用 GitHub CLI
gh secret set GCP_SA_KEY < github-deployer-key.json

# 驗證
gh secret list
```

#### 設定 Variables

```bash
# 使用 GitHub CLI
gh variable set REGISTRY_HOST --body "us-central1-docker.pkg.dev"
gh variable set GCP_PROJECT_ID --body "$PROJECT_ID"
gh variable set GAR_REPOSITORY --body "images"
gh variable set GCE_INSTANCE --body "refactor-agent-prod"
gh variable set GCE_ZONE --body "us-central1-a"
gh variable set VITE_API_BASE_URL --body "http://YOUR_INSTANCE_IP:8000"

# 驗證
gh variable list
```

### Step 4: 初始化 GCE 實例

#### 4.1 SSH 到實例

```bash
gcloud compute ssh refactor-agent-prod --zone=us-central1-a --project=$PROJECT_ID
```

#### 4.2 安裝 Docker & Docker Compose

```bash
# Container-Optimized OS 已預裝 Docker
# 如果是 Ubuntu/Debian，執行：
sudo apt-get update
sudo apt-get install -y docker.io docker-compose

# 將當前使用者加入 docker group
sudo usermod -aG docker $USER
```

#### 4.3 設定 Docker 認證

```bash
# 在 GCE 實例上設定 gcloud
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
```

#### 4.4 部署專案檔案

```bash
# Clone 專案
cd ~
git clone https://github.com/YOUR_USERNAME/auto-refactor-agent.git
cd auto-refactor-agent

# 建立 backend/.env 檔案（API 容器會讀取）
mkdir -p backend
cat > backend/.env << 'EOF'
# MongoDB
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DATABASE=refactor_agent

# PostgreSQL（必填）
POSTGRES_URL=postgresql://langgraph:langgraph_secret@postgres:5432/langgraph

# JWT 認證
JWT_SECRET_KEY=CHANGE_THIS_TO_A_SECURE_RANDOM_STRING_IN_PRODUCTION
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24

# Anthropic API
ANTHROPIC_API_KEY=YOUR_ANTHROPIC_API_KEY_HERE

# Docker
DOCKER_BASE_IMAGE=refactor-base:latest
DOCKER_NETWORK=refactor-network
# 專案 workspace 在 API 容器內的根目錄（host 端目錄由 compose 的 WORKSPACE_HOST_DIR 控制）
DOCKER_VOLUME_PREFIX=/tmp/refactor-workspaces

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
chmod 600 backend/.env
```

⚠️ **重要**：請修改 `backend/.env` 中的以下變數：
- `JWT_SECRET_KEY` - 生產環境務必使用安全的隨機字串
- `ANTHROPIC_API_KEY` - 填入你的 Anthropic API Key

#### 4.5 建立 Docker 網路

```bash
docker network create refactor-network
```

#### 4.6 測試部署

```bash
# 設定部署必要環境變數（用於組成 image name）
export REGISTRY_HOST="us-central1-docker.pkg.dev"
export GCP_PROJECT_ID="$PROJECT_ID"
export GAR_REPOSITORY="images"
export IMAGE_TAG="latest"

# (可選) host 端 workspace 目錄
export WORKSPACE_HOST_DIR="/var/lib/refactor-workspaces"

# 一鍵拉取並啟動服務
./scripts/deploy-prod.sh
```

---

## 🎯 觸發部署

### 自動部署（推薦）

當你 push 程式碼到 main 分支時會自動部署：

```bash
git add .
git commit -m "feat: 新功能"
git push origin main
```

部署流程會自動執行：
1. ✅ CI 測試（Backend + Frontend）
2. ✅ 建置並推送映像到 GAR
3. ✅ 自動部署到 GCE
4. ✅ 健康檢查

### 手動部署

使用 GitHub Actions UI：

1. 前往 `Actions > Deploy to GCE`
2. 點擊 `Run workflow`
3. 點擊 `Run workflow` 確認

或使用 GitHub CLI：

```bash
gh workflow run deploy-gce.yml
```

---

## ✅ 驗證部署

### 1. 檢查 GitHub Actions 狀態

```bash
# 查看最新的 workflow runs
gh run list --workflow=deploy-gce.yml --limit 5

# 查看特定 run 的詳細日誌
gh run view RUN_ID --log
```

### 2. 檢查 GCE 服務狀態

```bash
# SSH 到實例
gcloud compute ssh refactor-agent-prod --zone=us-central1-a

# 檢查容器狀態
docker ps

# 檢查 API 日誌
docker logs refactor-api --tail 100

# 檢查 Frontend 日誌
docker logs refactor-frontend --tail 100

# 檢查 MongoDB 日誌
docker logs refactor-mongodb --tail 100

# 檢查 PostgreSQL 日誌
docker logs refactor-postgres --tail 100
```

### 3. 測試服務端點

```bash
# 取得外部 IP
EXTERNAL_IP=$(gcloud compute instances describe refactor-agent-prod \
  --zone=us-central1-a \
  --project=$PROJECT_ID \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "Instance IP: $EXTERNAL_IP"

# 測試 API health endpoint
curl http://$EXTERNAL_IP:8000/api/v1/health

# 測試 Frontend
curl -I http://$EXTERNAL_IP:80
```

---

## 🔧 故障排除

### 問題 1: Service Account 權限不足

**錯誤訊息**：
```
Error: Permission denied to access resource
```

**解決方案**：
```bash
# 檢查 Service Account 權限
gcloud projects get-iam-policy $PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:github-deployer@${PROJECT_ID}.iam.gserviceaccount.com"

# 重新授予權限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/compute.instanceAdmin.v1"
```

### 問題 2: GCE SSH 連接失敗

**錯誤訊息**：
```
Error: Unable to connect to GCE instance
```

**解決方案**：
```bash
# 測試 SSH 連接
gcloud compute ssh refactor-agent-prod \
  --zone=us-central1-a \
  --project=$PROJECT_ID \
  --dry-run

# 檢查防火牆規則
gcloud compute firewall-rules list --project=$PROJECT_ID

# 檢查實例狀態
gcloud compute instances describe refactor-agent-prod \
  --zone=us-central1-a \
  --project=$PROJECT_ID
```

### 問題 3: Docker 映像拉取失敗

**錯誤訊息**：
```
Error: Failed to pull image from GAR
```

**解決方案**：
```bash
# SSH 到 GCE
gcloud compute ssh refactor-agent-prod --zone=us-central1-a

# 重新設定 Docker 認證
gcloud auth configure-docker us-central1-docker.pkg.dev

# 手動測試拉取
docker pull us-central1-docker.pkg.dev/$PROJECT_ID/images/refactor-base:latest
```

### 問題 4: 健康檢查失敗

**解決方案**：
```bash
# SSH 到 GCE
gcloud compute ssh refactor-agent-prod --zone=us-central1-a

# 檢查所有容器狀態
docker ps -a

# 檢查 API 容器日誌
docker logs refactor-api --tail 50

# 檢查網路連接
docker exec refactor-api curl -f http://localhost:8000/api/v1/health

# 檢查防火牆
sudo iptables -L -n
```

### 問題 5: POSTGRES_URL 錯誤

**錯誤訊息**：
```
ValueError: PostgreSQL URL is required
```

**解決方案**：
```bash
# SSH 到 GCE
gcloud compute ssh refactor-agent-prod --zone=us-central1-a

# 檢查 backend/.env
cat ~/auto-refactor-agent/backend/.env | grep POSTGRES_URL

# 確保 PostgreSQL 容器正在運行
docker ps | grep postgres

# 重啟服務
cd ~/auto-refactor-agent
docker compose -f devops/docker-compose.prod.yml restart api
```

---

## 🔄 回滾部署

如果新版本有問題，可以回滾到舊版本：

```bash
# SSH 到 GCE
gcloud compute ssh refactor-agent-prod --zone=us-central1-a

# 切換到專案目錄
cd ~/auto-refactor-agent

# 拉取舊版本映像（使用舊的 commit SHA）
OLD_TAG="abc1234"  # 替換為舊的 commit SHA (前 7 位)

docker pull us-central1-docker.pkg.dev/$PROJECT_ID/images/refactor-base:$OLD_TAG
docker pull us-central1-docker.pkg.dev/$PROJECT_ID/images/refactor-api:$OLD_TAG
docker pull us-central1-docker.pkg.dev/$PROJECT_ID/images/refactor-frontend:$OLD_TAG

# 使用舊 tag 重新啟動（確保 docker compose 變數對應）
export REGISTRY_HOST="us-central1-docker.pkg.dev"
export GCP_PROJECT_ID="$PROJECT_ID"
export GAR_REPOSITORY="images"
export IMAGE_TAG="$OLD_TAG"

./scripts/deploy-prod.sh

# 驗證
docker compose -f devops/docker-compose.prod.yml ps
```

---

## 🔒 安全建議

### 1. Service Account 權限最小化

只授予必要的最小權限，不要使用 Owner 或 Editor 角色。

### 2. 定期更新

```bash
# 定期輪換 Service Account Keys
gcloud iam service-accounts keys list \
  --iam-account=github-deployer@${PROJECT_ID}.iam.gserviceaccount.com

# 刪除舊的 keys
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=github-deployer@${PROJECT_ID}.iam.gserviceaccount.com
```

### 3. 啟用 HTTPS

使用 Let's Encrypt 或 Google-managed SSL certificates：

```bash
# 安裝 Certbot
sudo apt-get install certbot python3-certbot-nginx

# 取得 SSL 證書
sudo certbot --nginx -d yourdomain.com
```

### 4. 限制網路訪問

```bash
# 建立更嚴格的防火牆規則
gcloud compute firewall-rules create allow-http-from-specific-ip \
  --allow=tcp:80,tcp:443,tcp:8000 \
  --source-ranges=YOUR_IP/32 \
  --target-tags=http-server
```

### 5. 備份資料

```bash
# 定期備份 MongoDB 和 PostgreSQL
# 可以使用 Cloud Storage 或設定自動快照
gcloud compute disks snapshot DISK_NAME \
  --zone=us-central1-a \
  --snapshot-names=backup-$(date +%Y%m%d-%H%M%S)
```

---

## 📊 監控與日誌

### Cloud Logging

```bash
# 查看 GCE 實例日誌
gcloud logging read "resource.type=gce_instance \
  AND resource.labels.instance_id=YOUR_INSTANCE_ID" \
  --limit 50 \
  --format json
```

### Cloud Monitoring

建議設定以下告警：
- CPU 使用率 > 80%
- 記憶體使用率 > 80%
- 磁碟使用率 > 90%
- HTTP 5xx 錯誤率 > 1%

---

## 📚 相關文檔

- [CI/CD Pipeline 說明](./README.md)
- [Docker Compose 配置](../../devops/docker-compose.prod.yml)
- [Backend 環境變數](../../backend/.env.example)
- [PostgreSQL 持久化說明](../../docs/BACKEND.md)

---

**最後更新**: 2026-02-06
**維護者**: Development Team

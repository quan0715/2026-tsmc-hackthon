# GitHub Secrets & Variables 檢查清單

快速參考：設定 GitHub Actions 所需的所有 secrets 和 variables。

---

## 📋 Secrets（機密資訊）

前往：`Settings > Secrets and variables > Actions > Secrets`

| Secret 名稱 | 用途 | 如何取得 | 必填 |
|-----------|------|---------|------|
| **GCP_SA_KEY** | GCP Service Account JSON Key | 執行 `gcloud iam service-accounts keys create` | ✅ |

### 取得 GCP_SA_KEY

```bash
# 1. 建立 Service Account
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer"

# 2. 授予權限
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/compute.instanceAdmin.v1"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"

# 3. 生成 JSON Key
gcloud iam service-accounts keys create github-deployer-key.json \
  --iam-account=github-deployer@YOUR_PROJECT_ID.iam.gserviceaccount.com

# 4. 複製整個 JSON 內容
cat github-deployer-key.json
```

**重要**：複製整個 JSON 檔案內容（包含 `{` 和 `}`），貼到 GitHub Secrets。

---

## 🔧 Variables（公開變數）

前往：`Settings > Secrets and variables > Actions > Variables`

### CI/CD & Build 相關

| 變數名稱 | 說明 | 範例值 | 必填 |
|---------|------|--------|------|
| **REGISTRY_HOST** | Google Artifact Registry 主機 | `us-central1-docker.pkg.dev` | ✅ |
| **GCP_PROJECT_ID** | GCP 專案 ID | `your-project-id` | ✅ |
| **GAR_REPOSITORY** | GAR Repository 名稱 | `images` | ✅ |
| **VITE_API_BASE_URL** | Frontend API URL（開發環境） | `http://localhost:8000` | ✅ |

### GCE 部署相關（Production）

| 變數名稱 | 說明 | 範例值 | 必填 |
|---------|------|--------|------|
| **GCE_INSTANCE_PROD** | Production GCE 實例名稱 | `refactor-agent-prod` | ✅ |
| **GCE_ZONE_PROD** | Production GCE 區域 | `us-central1-a` | ✅ |

### GCE 部署相關（Staging - 可選）

| 變數名稱 | 說明 | 範例值 | 必填 |
|---------|------|--------|------|
| **GCE_INSTANCE_STAGING** | Staging GCE 實例名稱 | `refactor-agent-staging` | ❌ |
| **GCE_ZONE_STAGING** | Staging GCE 區域 | `us-central1-a` | ❌ |

---

## 🚀 快速設定步驟

### 1. 建立 GCP 資源

```bash
# 設定變數
export PROJECT_ID="your-project-id"
export REGION="us-central1"
export ZONE="${REGION}-a"

# 建立 Artifact Registry
gcloud artifacts repositories create images \
  --repository-format=docker \
  --location=$REGION \
  --project=$PROJECT_ID

# 建立 GCE 實例
gcloud compute instances create refactor-agent-prod \
  --zone=$ZONE \
  --machine-type=n1-standard-2 \
  --image-family=cos-stable \
  --image-project=cos-cloud \
  --boot-disk-size=50GB \
  --tags=http-server,https-server \
  --project=$PROJECT_ID

# 設定防火牆
gcloud compute firewall-rules create allow-http \
  --allow=tcp:80 \
  --target-tags=http-server \
  --project=$PROJECT_ID

gcloud compute firewall-rules create allow-api \
  --allow=tcp:8000 \
  --target-tags=http-server \
  --project=$PROJECT_ID
```

### 2. 建立 Service Account

```bash
# 建立 SA
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Actions Deployer" \
  --project=$PROJECT_ID

# 授予權限
for role in "roles/artifactregistry.writer" \
            "roles/compute.instanceAdmin.v1" \
            "roles/iam.serviceAccountUser"; do
  gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:github-deployer@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="$role"
done

# 生成 Key
gcloud iam service-accounts keys create github-deployer-key.json \
  --iam-account=github-deployer@${PROJECT_ID}.iam.gserviceaccount.com

echo "✅ Service Account Key 已儲存到 github-deployer-key.json"
echo "請複製此檔案內容到 GitHub Secrets (GCP_SA_KEY)"
```

### 3. 設定 GitHub Secrets

```bash
# 顯示需要複製的內容
echo "📋 複製以下內容到 GitHub Secrets:"
echo ""
cat github-deployer-key.json
```

前往 GitHub Repository:
1. `Settings` > `Secrets and variables` > `Actions` > `Secrets`
2. 點擊 `New repository secret`
3. Name: `GCP_SA_KEY`
4. Value: 貼上上面的 JSON 內容
5. 點擊 `Add secret`

### 4. 設定 GitHub Variables

前往 GitHub Repository:
1. `Settings` > `Secrets and variables` > `Actions` > `Variables`
2. 點擊 `New repository variable`

新增以下 variables：

```
REGISTRY_HOST = us-central1-docker.pkg.dev
GCP_PROJECT_ID = your-project-id
GAR_REPOSITORY = images
VITE_API_BASE_URL = http://localhost:8000
GCE_INSTANCE_PROD = refactor-agent-prod
GCE_ZONE_PROD = us-central1-a
```

---

## ✅ 驗證設定

### 檢查 Secrets

```bash
# 使用 GitHub CLI
gh secret list

# 預期輸出：
# GCP_SA_KEY  Updated YYYY-MM-DD
```

### 檢查 Variables

```bash
# 使用 GitHub CLI
gh variable list

# 預期輸出：
# REGISTRY_HOST           us-central1-docker.pkg.dev  Updated YYYY-MM-DD
# GCP_PROJECT_ID          your-project-id             Updated YYYY-MM-DD
# GAR_REPOSITORY          images                      Updated YYYY-MM-DD
# VITE_API_BASE_URL       http://localhost:8000       Updated YYYY-MM-DD
# GCE_INSTANCE_PROD       refactor-agent-prod         Updated YYYY-MM-DD
# GCE_ZONE_PROD           us-central1-a               Updated YYYY-MM-DD
```

### 測試 Workflow

```bash
# 手動觸發 CI/CD Pipeline
gh workflow run build-and-push.yml

# 查看執行狀態
gh run list --workflow=build-and-push.yml
```

---

## 🔒 安全注意事項

### ✅ 推薦做法

- ✅ 使用專用的 Service Account
- ✅ 只授予必要的最小權限
- ✅ 定期輪換 Service Account Keys
- ✅ 限制 GCE 實例的網路訪問
- ✅ 使用私有 IP（搭配 Cloud NAT）

### ❌ 避免做法

- ❌ 不要使用個人帳號的 credentials
- ❌ 不要授予 Owner 或 Editor 角色
- ❌ 不要提交 Service Account Key 到 Git
- ❌ 不要在 public repository 使用 Variables 儲存敏感資訊

---

## 📚 相關文檔

- [完整部署設定指南](./DEPLOY_SETUP.md)
- [CI/CD Pipeline 說明](./README.md)
- [GCP IAM 文檔](https://cloud.google.com/iam/docs)
- [GitHub Actions Secrets 文檔](https://docs.github.com/en/actions/security-guides/encrypted-secrets)

---

**最後更新**: 2026-02-06

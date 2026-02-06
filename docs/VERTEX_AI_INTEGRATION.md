# Vertex AI 整合計劃

## 🎯 整合目標

支援透過 Google Cloud Vertex AI 使用 LLM 模型，提供多種模型選擇：

| Provider | 模型 | 說明 |
|----------|------|------|
| **anthropic** | Claude Haiku 4.5 / Sonnet 4.5 | 直接使用 Anthropic API（目前使用） |
| **vertex-anthropic** | Claude Sonnet 4.5 | 透過 Vertex AI 使用 Claude（Anthropic on Vertex） |
| **vertex-gemini** | Gemini 2.5 Pro | 透過 Vertex AI 使用 Google Gemini |

---

## 📊 現況分析

### ✅ 已具備的基礎

1. **VertexModelProvider 類別** (`agent/models.py`)
   - 已實作 `get_anthropic_vertex_model()` - Claude on Vertex AI
   - 已實作 `get_gemini_vertex_model()` - Gemini
   - 支援 Service Account 認證

2. **環境變數配置** (`.env`)
   - `GCP_PROJECT_ID = cloud-native-458808`
   - `GOOGLE_APPLICATION_CREDENTIALS` 路徑已定義

3. **CI/CD 管道**
   - GitHub Actions workflows 完整
   - Docker 容器動態環境變數注入機制
   - GCE 自動部署流程

### 🔧 需要整合的部分

1. **模型初始化層**
   - 目前硬編碼使用 `AnthropicModelProvider`
   - 需要新增工廠方法支援多 provider

2. **環境變數傳遞**
   - 容器服務需要傳遞 Vertex AI 相關環境變數
   - Service Account credentials 需要安全掛載

3. **配置檔案**
   - 環境變數範例需要更新
   - 部署文檔需要新增 Vertex AI 設定說明

---

## 📋 實作步驟

### Step 1: 模型層改造

**檔案**: `agent/models.py`

新增工廠方法：

```python
def get_model(provider: str = "anthropic"):
    """工廠方法：根據 provider 選擇 LLM

    Args:
        provider: "anthropic" | "vertex-anthropic" | "vertex-gemini"

    Returns:
        LLM instance

    Raises:
        ValueError: 如果 provider 未知或缺少必要配置
    """
    if provider == "anthropic":
        return AnthropicModelProvider().get_model()

    elif provider == "vertex-anthropic":
        project = os.getenv("GCP_PROJECT_ID")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not project or not credentials_path:
            raise ValueError(
                "GCP_PROJECT_ID and GOOGLE_APPLICATION_CREDENTIALS are required for Vertex AI"
            )

        vertex_provider = VertexModelProvider(project, credentials_path)
        return vertex_provider.get_anthropic_vertex_model()

    elif provider == "vertex-gemini":
        project = os.getenv("GCP_PROJECT_ID")
        credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

        if not project or not credentials_path:
            raise ValueError(
                "GCP_PROJECT_ID and GOOGLE_APPLICATION_CREDENTIALS are required for Vertex AI"
            )

        vertex_provider = VertexModelProvider(project, credentials_path)
        return vertex_provider.get_gemini_vertex_model()

    else:
        raise ValueError(f"Unknown provider: {provider}")
```

**變更清單**：
- [ ] 新增 `get_model()` 工廠方法
- [ ] 從環境變數讀取 provider 選擇
- [ ] 支援三種 provider 切換

---

### Step 2: Agent 初始化更新

**檔案**: `agent/server/handlers.py`

修改第 70 和 201 行：

```python
# 舊版
from agent.models import AnthropicModelProvider
provider = AnthropicModelProvider()
model = provider.get_model()

# 新版
from agent.models import get_model
provider = os.environ.get("MODEL_PROVIDER", "anthropic")
model = get_model(provider)
```

**變更清單**：
- [ ] 修改 `execute_agent()` 中的模型初始化
- [ ] 修改 `execute_chat()` 中的模型初始化
- [ ] 新增環境變數讀取邏輯

---

### Step 3: 依賴套件更新

**檔案**: `agent/requirements.txt`

新增：

```txt
# Vertex AI support
langchain-google-vertexai>=2.0.0
```

**變更清單**：
- [ ] 新增 `langchain-google-vertexai` 依賴
- [ ] 更新 base image Dockerfile 以包含新依賴

---

### Step 4: 容器環境變數注入

**檔案**: `backend/app/services/container_service.py`

在第 60-72 行後新增：

```python
# 傳遞 MODEL_PROVIDER
if hasattr(settings, 'model_provider') and settings.model_provider:
    env_vars.extend(["-e", f"MODEL_PROVIDER={settings.model_provider}"])
    logger.info(f"容器將使用 Model Provider: {settings.model_provider}")

# 如果使用 Vertex AI，傳遞 GCP 相關變數
if hasattr(settings, 'model_provider') and settings.model_provider.startswith('vertex'):
    if hasattr(settings, 'gcp_project_id') and settings.gcp_project_id:
        env_vars.extend(["-e", f"GCP_PROJECT_ID={settings.gcp_project_id}"])

    # 掛載 Service Account JSON
    if hasattr(settings, 'google_application_credentials') and settings.google_application_credentials:
        host_creds_path = settings.google_application_credentials
        container_creds_path = "/workspace/agent/gcp-credentials.json"
        volume_args.extend(["-v", f"{host_creds_path}:{container_creds_path}:ro"])
        env_vars.extend(["-e", f"GOOGLE_APPLICATION_CREDENTIALS={container_creds_path}"])
        logger.info("容器將掛載 GCP Service Account credentials")
```

**變更清單**：
- [ ] 新增 `MODEL_PROVIDER` 環境變數傳遞
- [ ] 新增 `GCP_PROJECT_ID` 環境變數傳遞
- [ ] 新增 Service Account credentials 檔案掛載邏輯
- [ ] 新增錯誤處理和日誌記錄

---

### Step 5: Backend 配置更新

**檔案**: `backend/app/config.py`

新增配置項：

```python
# Model Provider 選擇
model_provider: str = "anthropic"  # "anthropic" | "vertex-anthropic" | "vertex-gemini"

# Vertex AI 設定（當 model_provider 為 vertex-* 時必填）
gcp_project_id: str = ""
gcp_location: str = "us-central1"
vertex_ai_model: str = "gemini-2.5-pro"
google_application_credentials: Optional[str] = None
```

**變更清單**：
- [ ] 新增 `model_provider` 配置項
- [ ] 新增 Vertex AI 相關配置項
- [ ] 更新註解說明必填條件

---

### Step 6: 環境變數範例更新

**檔案**: `backend/.env.example`

```bash
# ==================== LLM 設定 ====================

# Model Provider（選擇一個）
# - anthropic: 直接使用 Anthropic API
# - vertex-anthropic: 透過 Vertex AI 使用 Claude
# - vertex-gemini: 透過 Vertex AI 使用 Gemini
MODEL_PROVIDER=anthropic

# Anthropic API（當 MODEL_PROVIDER=anthropic 時必填）
ANTHROPIC_API_KEY=your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# Vertex AI 設定（當 MODEL_PROVIDER=vertex-* 時必填）
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
VERTEX_AI_MODEL=gemini-2.5-pro
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

**檔案**: `agent/.env.example`

```bash
# ==================== 必填項目 ====================

# PostgreSQL（會話持久化 - 必填）
POSTGRES_URL=postgresql://langgraph:langgraph_secret@postgres:5432/langgraph

# Model Provider
MODEL_PROVIDER=anthropic

# ==================== Anthropic API ====================
# 當 MODEL_PROVIDER=anthropic 時必填
ANTHROPIC_API_KEY=your-anthropic-api-key-here
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# ==================== Vertex AI ====================
# 當 MODEL_PROVIDER=vertex-* 時必填
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/workspace/agent/gcp-credentials.json
```

**變更清單**：
- [ ] 更新 `backend/.env.example`
- [ ] 更新 `agent/.env.example`
- [ ] 新增詳細的配置說明和範例

---

### Step 7: Service Account 管理

**方案 A：掛載 JSON 檔案**（推薦用於開發）

```bash
# 在 GCE 實例上
mkdir -p /var/lib/refactor-credentials
# 上傳 Service Account JSON
scp service-account-key.json gce-instance:/var/lib/refactor-credentials/

# 在 .env.prod 中設定
GOOGLE_APPLICATION_CREDENTIALS=/var/lib/refactor-credentials/service-account-key.json
```

**方案 B：使用 GCE 預設 Service Account**（推薦用於生產）

修改 `agent/models.py` 中的 `VertexModelProvider`:

```python
def load_credentials(self, credentials_path: str = None):
    if credentials_path and os.path.exists(credentials_path):
        # 使用指定的 Service Account JSON
        self.credentials = Credentials.from_service_account_file(
            credentials_path,
            scopes=["https://www.googleapis.com/auth/cloud-platform"],
        )
    else:
        # 使用 GCE 預設 credentials（Application Default Credentials）
        from google.auth import default
        self.credentials, _ = default(
            scopes=["https://www.googleapis.com/auth/cloud-platform"]
        )
```

**變更清單**：
- [ ] 支援檔案路徑方式載入 credentials
- [ ] 支援 Application Default Credentials (ADC)
- [ ] 新增錯誤處理和日誌記錄
- [ ] 撰寫 Service Account 設定指南

---

### Step 8: CI/CD 整合

**檔案**: `.github/workflows/deploy-gce.yml`

新增環境變數和 credentials 處理：

```yaml
- name: Deploy to GCE
  run: |
    # 如果使用 Vertex AI，上傳 Service Account key
    if [ "${{ vars.MODEL_PROVIDER }}" = "vertex-anthropic" ] || [ "${{ vars.MODEL_PROVIDER }}" = "vertex-gemini" ]; then
      echo "📦 Uploading GCP credentials to GCE..."
      gcloud compute scp <(echo '${{ secrets.GCP_VERTEX_SA_KEY }}') \
        ${{ env.GCE_INSTANCE }}:/var/lib/refactor-credentials/service-account-key.json \
        --zone=${{ env.GCE_ZONE }} \
        --project=${{ env.GCP_PROJECT_ID }}
    fi
```

**GitHub Variables 設定**：

```bash
# 設定 Model Provider
gh variable set MODEL_PROVIDER --body "vertex-gemini"

# 設定 GCP Project ID
gh variable set VERTEX_PROJECT_ID --body "cloud-native-458808"
```

**GitHub Secrets 設定**（選用）：

```bash
# 如果要使用 Service Account JSON
gh secret set GCP_VERTEX_SA_KEY < service-account-key.json
```

**變更清單**：
- [ ] 修改 `deploy-gce.yml` 支援 Vertex AI credentials 部署
- [ ] 新增 GitHub Variables 配置
- [ ] 新增 GitHub Secrets 配置（選用）
- [ ] 更新部署文檔

---

### Step 9: 文檔更新

**新增文檔**：

1. **Vertex AI 設定指南** (`docs/VERTEX_AI_SETUP.md`)
   - Service Account 建立步驟
   - 權限配置指南
   - 本地開發設定
   - GCE 生產環境設定

2. **切換指南** (`docs/VERTEX_AI_SWITCH.md`)
   - 如何在不同 provider 間切換
   - 常見問題排除
   - 效能和成本比較

**更新現有文檔**：

1. **README.md**
   - 新增 Vertex AI 支援說明
   - 更新環境變數配置章節

2. **GCE_DEPLOY.md**
   - 新增 Vertex AI 部署步驟
   - 新增 Service Account 配置章節

**變更清單**：
- [ ] 新增 `docs/VERTEX_AI_SETUP.md`
- [ ] 新增 `docs/VERTEX_AI_SWITCH.md`
- [ ] 更新 `README.md`
- [ ] 更新 `.github/workflows/GCE_DEPLOY.md`

---

### Step 10: 測試與驗證

**本地測試**：

```bash
# 測試 Anthropic provider
MODEL_PROVIDER=anthropic docker-compose up api

# 測試 Vertex AI - Claude
MODEL_PROVIDER=vertex-anthropic docker-compose up api

# 測試 Vertex AI - Gemini
MODEL_PROVIDER=vertex-gemini docker-compose up api
```

**驗證清單**：

- [ ] 三種 provider 都能正常初始化
- [ ] 環境變數正確傳遞到容器
- [ ] Service Account credentials 正確掛載
- [ ] Agent 可以正常對話
- [ ] PostgreSQL 持久化正常運作
- [ ] 日誌顯示正確的模型資訊

**GCE 部署測試**：

- [ ] 部署腳本正確執行
- [ ] Credentials 正確上傳到 GCE
- [ ] 容器使用正確的 provider
- [ ] 健康檢查通過
- [ ] API 端點正常回應

---

## 🔒 安全考量

### Service Account 權限

建議授予的最小權限：

```bash
# Vertex AI 使用權限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/aiplatform.user"

# 如果使用 Anthropic on Vertex
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:$SA_EMAIL" \
  --role="roles/aiplatform.modelGardenUser"
```

### Credentials 保護

- ✅ 本地開發使用 `.env` 檔案（不提交到 Git）
- ✅ 生產環境使用 GitHub Secrets
- ✅ 容器掛載使用 read-only (`:ro`) 模式
- ✅ GCE 生產環境考慮使用 ADC（不需要 JSON 檔案）

---

## 📊 效能與成本比較

| Provider | 延遲 | 成本 | 區域可用性 | 備註 |
|----------|------|------|-----------|------|
| **Anthropic API** | 低 | 中 | 全球 | 目前使用 |
| **Claude on Vertex** | 中 | 中-高 | us-east5 | 需要 Vertex AI 配額 |
| **Gemini** | 低 | 低-中 | 多區域 | Google 原生整合 |

---

## 🚀 遷移計劃

### Phase 1: 開發環境測試（1-2 天）
- 實作所有程式碼變更
- 本地測試三種 provider
- 驗證基本功能

### Phase 2: CI/CD 整合（1 天）
- 更新 GitHub Actions
- 配置環境變數
- 測試自動部署

### Phase 3: 生產環境試運行（1-2 天）
- 部署到 GCE staging（如有）
- 效能測試和監控
- 成本分析

### Phase 4: 正式切換（視需求）
- 評估是否切換到 Vertex AI
- 逐步遷移或並行運作
- 監控和調優

---

## ✅ 完成標準

- [ ] 所有程式碼變更完成並測試通過
- [ ] CI/CD pipeline 正常運作
- [ ] 文檔完整且準確
- [ ] 安全性審查通過
- [ ] 效能測試達標
- [ ] 部署到生產環境驗證成功

---

**建立日期**: 2026-02-06
**最後更新**: 2026-02-06
**狀態**: 🚧 規劃中
**負責人**: Development Team

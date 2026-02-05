# GitHub Actions CI/CD Pipeline

## 概述

本專案使用 GitHub Actions 實作完整的 CI/CD pipeline，包含測試驗證和 Docker 映像建置推送。

---

## Pipeline 架構

```
┌─────────────────────────────────────────────────┐
│  Trigger: Push to main / PR / Manual dispatch  │
└─────────────────┬───────────────────────────────┘
                  │
         ┌────────▼─────────┐
         │   Job 1: CI      │
         │  Tests & Lint    │
         └────────┬─────────┘
                  │
         ┌────────▼─────────┐
         │ Backend Tests    │
         │ - pytest         │
         │ - Unit tests     │
         │ - Integration    │
         └────────┬─────────┘
                  │
         ┌────────▼─────────┐
         │ Frontend CI      │
         │ - npm ci         │
         │ - npm build      │
         │ - npm test       │
         │ - npm lint       │
         └────────┬─────────┘
                  │
        ┌─────────▼──────────┐
        │ Job 2: Build-Push  │
        │  (depends on CI)   │
        └─────────┬──────────┘
                  │
         ┌────────▼─────────┐
         │ Docker Build     │
         │ - Base Image     │
         │ - API Image      │
         │ - Frontend Image │
         └──────────────────┘
```

---

## Jobs 說明

### Job 1: CI - Tests & Linting

**目的**: 驗證程式碼品質和功能正確性

**執行內容**:

#### Backend 測試
- ✅ 設置 Python 3.11 環境
- ✅ 安裝 backend 和 agent 依賴
- ✅ 執行 pytest 測試套件
- ✅ 使用測試資料庫（PostgreSQL + MongoDB）

#### Frontend 測試
- ✅ 設置 Node.js 20 環境
- ✅ 執行 `npm ci` 安裝依賴
- ✅ 執行 `npm run build` 驗證建置
- ✅ 執行 `npm run test` 單元測試
- ✅ 執行 `npm run lint` 程式碼檢查

**服務依賴**:
- PostgreSQL 16（用於 Agent 持久化測試）
- MongoDB 7（用於資料庫測試）

**環境變數**:
```yaml
MONGODB_URL: mongodb://localhost:27017
POSTGRES_URL: postgresql://langgraph:langgraph_secret@localhost:5432/langgraph
JWT_SECRET_KEY: test-secret-key-for-ci
ANTHROPIC_API_KEY: sk-ant-test-dummy-key-for-ci
```

---

### Job 2: Build & Push Docker Images

**目的**: 建置並推送 Docker 映像到 Google Artifact Registry

**執行條件**:
- ✅ CI Job 必須通過（`needs: ci`）
- ✅ 所有測試和驗證成功

**映像清單**:
1. **Base Image** (`refactor-base`)
   - 包含 Agent 程式碼和依賴
   - 檔案: `devops/base-image/Dockerfile`

2. **API Image** (`refactor-api`)
   - Backend FastAPI 應用
   - 檔案: `backend/Dockerfile.prod`

3. **Frontend Image** (`refactor-frontend`)
   - React 前端應用
   - 檔案: `frontend/Dockerfile.prod`

**推送策略**:
- **PR / Push**: 僅建置驗證，不推送
- **Manual Dispatch**: 建置並推送到 GAR

---

## 觸發條件

### 1. Push to main
```bash
git push origin main
```
- ✅ 執行完整 CI 測試
- ✅ 驗證 Docker 建置
- ❌ 不推送映像

### 2. Pull Request
```bash
gh pr create --base main
```
- ✅ 執行完整 CI 測試
- ✅ 驗證 Docker 建置
- ❌ 不推送映像

### 3. Manual Dispatch
```bash
# 透過 GitHub UI 手動觸發
Actions > CI/CD Pipeline > Run workflow
```
- ✅ 執行完整 CI 測試
- ✅ 建置 Docker 映像
- ✅ 推送映像到 GAR

---

## 環境變數設定

### Repository Variables (公開)

在 GitHub Repository Settings > Secrets and variables > Actions > Variables 中設定：

| 變數名稱 | 說明 | 範例 |
|---------|------|------|
| `REGISTRY_HOST` | GAR 主機名稱 | `us-central1-docker.pkg.dev` |
| `GCP_PROJECT_ID` | GCP 專案 ID | `your-project-id` |
| `GAR_REPOSITORY` | GAR Repository | `images` |
| `VITE_API_BASE_URL` | Frontend API URL | `http://localhost:8000` |

### Repository Secrets (機密)

在 GitHub Repository Settings > Secrets and variables > Actions > Secrets 中設定：

| Secret 名稱 | 說明 | 用途 |
|-----------|------|------|
| `GCP_SA_KEY` | GCP Service Account Key (JSON) | 推送映像到 GAR |

---

## 本地測試

### 執行 Backend 測試

```bash
# 啟動服務
docker-compose -f devops/docker-compose.yml up -d postgres mongodb

# 設定環境變數
export MONGODB_URL="mongodb://localhost:27017"
export POSTGRES_URL="postgresql://langgraph:langgraph_secret@localhost:5432/langgraph"
export JWT_SECRET_KEY="test-secret-key"
export ANTHROPIC_API_KEY="sk-ant-test-dummy-key"

# 執行測試
cd backend
pytest tests/ -v
```

### 執行 Frontend 測試

```bash
cd frontend

# 安裝依賴
npm ci

# 執行建置
npm run build

# 執行測試
npm run test

# 執行 Linting
npm run lint
```

---

## 測試覆蓋率

### Backend
- Unit Tests: `backend/tests/unit/`
- Integration Tests: `backend/tests/integration/`
- E2E Tests: `backend/tests/e2e/`

### Frontend
- Component Tests: `frontend/src/**/__tests__/`
- Hook Tests: `frontend/src/hooks/__tests__/`

---

## 故障排除

### CI 測試失敗

**Backend 測試失敗**:
```bash
# 檢查測試日誌
# 確認 PostgreSQL 和 MongoDB 服務正常
# 驗證環境變數設定正確
```

**Frontend 測試失敗**:
```bash
# 確認 package.json 和 package-lock.json 同步
npm install  # 更新 lock file
npm ci       # 驗證乾淨安裝
```

### Docker Build 失敗

**檢查清單**:
- [ ] CI Job 是否通過？
- [ ] Dockerfile 路徑是否正確？
- [ ] Context 是否正確設定？
- [ ] 依賴項是否完整？

---

## 最佳實踐

### 1. 在推送前本地測試

```bash
# Backend
cd backend && pytest tests/ -v

# Frontend
cd frontend && npm ci && npm run build && npm run test
```

### 2. 確保 package-lock.json 同步

```bash
cd frontend
npm install  # 更新 lock file
git add package-lock.json
git commit -m "chore: update package-lock.json"
```

### 3. 使用 PR 進行程式碼審查

```bash
# 建立 feature branch
git checkout -b feature/your-feature

# 推送並建立 PR
git push origin feature/your-feature
gh pr create --base main
```

### 4. Manual Dispatch 用於部署

- 僅在需要推送映像時使用
- 確認所有測試通過後再觸發
- 檢查映像 tag 和版本

---

## 相關文檔

- [Docker Compose 配置](../../devops/docker-compose.yml)
- [Backend 測試指南](../../backend/tests/QUICK_START.md)
- [Frontend 測試配置](../../frontend/vitest.config.ts)
- [環境變數配置](../../ENV_UPDATE_SUMMARY.md)

---

**最後更新**: 2026-02-06
**維護者**: Development Team

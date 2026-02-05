# 環境變數配置更新總結

**更新日期**: 2026-02-06

---

## 更新檔案

1. ✅ `backend/.env.example` - Backend API 環境變數範例
2. ✅ `agent/.env.example` - Agent 容器環境變數範例

---

## 主要變更

### 1. 新增必填項目

#### POSTGRES_URL（必填！）

```bash
# PostgreSQL（Agent 會話持久化 - 必填！）
# ⚠️ Agent 無法在沒有 PostgreSQL 的情況下運行
POSTGRES_URL=postgresql://langgraph:langgraph_secret@postgres:5432/langgraph
```

**原因**: 根據 PostgreSQL 統一持久化改造，Agent 現在強制需要 PostgreSQL 進行會話持久化。

**影響範圍**:
- `backend/.env.example` - Backend 需要此變數來啟動服務
- `agent/.env.example` - Agent 容器需要此變數來初始化 checkpointer

### 2. 簡化配置結構

#### 移除項目

- ❌ Vertex AI 相關配置（已移除，簡化配置）
- ❌ 過時的說明和註解

#### 保留必要項目

**backend/.env.example**:
- ✅ MongoDB 配置（資料持久化）
- ✅ PostgreSQL 配置（會話持久化）
- ✅ JWT 認證配置
- ✅ Anthropic API 配置
- ✅ Docker 配置
- ✅ 可選項目（API、容器資源、Git、Log 設定）

**agent/.env.example**:
- ✅ Anthropic API 配置
- ✅ PostgreSQL 配置
- ✅ 可選項目（模型設定）

---

## 配置說明

### backend/.env.example

```bash
# 必填項目（共 7 項）
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DATABASE=refactor_agent
POSTGRES_URL=postgresql://langgraph:langgraph_secret@postgres:5432/langgraph
JWT_SECRET_KEY=your-secret-key-change-in-production-please
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_HOURS=24
ANTHROPIC_API_KEY=your-anthropic-api-key-here
DOCKER_BASE_IMAGE=refactor-base:latest
DOCKER_NETWORK=refactor-network
DOCKER_VOLUME_PREFIX=/tmp/refactor-workspaces

# 可選項目（共 8 項）
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
DEBUG=false
CONTAINER_CPU_LIMIT=2.0
CONTAINER_MEMORY_LIMIT=2g
GIT_CLONE_TIMEOUT=300
GIT_DEPTH=1
LOG_LEVEL=INFO
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

### agent/.env.example

```bash
# 必填項目（共 2 項）
ANTHROPIC_API_KEY=your-anthropic-api-key-here
POSTGRES_URL=postgresql://langgraph:langgraph_secret@postgres:5432/langgraph

# 可選項目（共 1 項）
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
```

---

## 快速開始指南

### 開發環境設定

```bash
# 1. 複製環境變數範例
cd backend
cp .env.example .env

# 2. 編輯 .env，填入必要的 API Key
# 至少需要填入：
# - ANTHROPIC_API_KEY（必填）
# 其他變數使用預設值即可

# 3. 啟動所有服務（包含 PostgreSQL）
cd ..
docker-compose -f devops/docker-compose.yml up -d

# 4. 驗證 PostgreSQL 連接
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "SELECT 1"

# 5. 檢查服務狀態
docker-compose -f devops/docker-compose.yml ps
```

### 本地開發（不使用 Docker Compose）

```bash
# 1. 啟動 PostgreSQL
docker run -d --name refactor-postgres \
  -p 5432:5432 \
  -e POSTGRES_USER=langgraph \
  -e POSTGRES_PASSWORD=langgraph_secret \
  -e POSTGRES_DB=langgraph \
  postgres:16

# 2. 啟動 MongoDB
docker run -d --name refactor-mongodb \
  -p 27017:27017 \
  mongo:7

# 3. 設定環境變數
export POSTGRES_URL="postgresql://langgraph:langgraph_secret@localhost:5432/langgraph"
export MONGODB_URL="mongodb://localhost:27017"
export ANTHROPIC_API_KEY="your-api-key-here"

# 4. 啟動 Backend
cd backend
uvicorn app.main:app --reload
```

---

## 重要注意事項

### ⚠️ PostgreSQL 必填

從此版本開始，**PostgreSQL 是必需的**，不論開發或生產環境都必須配置。

**原因**: Agent 會話持久化機制已改為強制使用 PostgreSQL，不再支援記憶體模式 fallback。

### ⚠️ 生產環境安全

生產環境部署時，請務必：

1. **更換 JWT_SECRET_KEY** - 使用安全的隨機字串
2. **更換 PostgreSQL 密碼** - 不要使用預設的 `langgraph_secret`
3. **限制網路訪問** - 使用防火牆限制 PostgreSQL 和 MongoDB 的訪問
4. **啟用 HTTPS** - 前端和 API 都應使用 HTTPS

### ⚠️ API Key 保護

- **不要提交** `.env` 文件到版本控制
- `.env` 已加入 `.gitignore`
- 僅提交 `.env.example` 作為範例

---

## 相關文檔

- 📄 [Backend 技術文件](docs/BACKEND.md)
- 📄 [PostgreSQL 持久化驗證指南](docs/testing/POSTGRES_PERSISTENCE_VERIFICATION.md)
- 📄 [PostgreSQL 遷移總結](POSTGRES_MIGRATION_SUMMARY.md)
- 📄 [測試結果報告](TEST_RESULTS.md)

---

## 版本歷史

- **v2.0** (2026-02-06) - PostgreSQL 持久化改造，新增 POSTGRES_URL 必填項
- **v1.0** (2026-02-02) - 初始版本

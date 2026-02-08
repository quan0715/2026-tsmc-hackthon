# PostgreSQL 統一持久化改造 - 變更總結

**日期**: 2026-02-06
**版本**: 1.0

---

## 概述

將 Agent 會話持久化機制從「三層 fallback（SQLite → PostgreSQL → Memory）」改為「強制使用 PostgreSQL」，確保開發和生產環境的一致性。

## 動機

### 改造前的問題
1. **不一致性**: 開發環境可能使用記憶體模式，生產環境使用 PostgreSQL
2. **靜默降級**: PostgreSQL 失敗時會靜默切換到記憶體模式，用戶不知道資料未持久化
3. **冗餘程式碼**: SQLite checkpointing 與 PostgreSQL 持久化功能重疊

### 官方建議
根據 [LangGraph 最佳實踐 (2025)](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025)：
- 生產環境**必須使用** PostgresSaver / AsyncPostgresSaver
- InMemorySaver 僅適用於開發測試，不應用於生產

## 主要變更

### 1. 強制使用 PostgreSQL

**檔案**: `agent/deep_agent.py`

- ❌ **移除**: `enable_checkpointing`, `checkpoint_db` 參數
- ❌ **移除**: `_setup_memory_persistence()` 方法
- ❌ **移除**: SQLite 和 Memory 相關導入
- ✅ **新增**: `postgres_url` 參數檢查（必填）
- ✅ **改進**: `_setup_persistence()` 失敗時拋出明確錯誤

### 2. 環境變數檢查

**檔案**: `agent/server/handlers.py`, `agent/server/app.py`

```python
postgres_url = os.environ.get("POSTGRES_URL")
if not postgres_url:
    raise HTTPException(
        status_code=500,
        detail="POSTGRES_URL environment variable is not set. PostgreSQL persistence is required."
    )
```

### 3. 依賴套件更新

**檔案**: `agent/requirements.txt`

```diff
- langgraph-checkpoint-postgres>=3.0.0  # Optional: PostgreSQL persistence
+ langgraph-checkpoint-postgres>=3.0.0  # Required: PostgreSQL persistence
```

### 4. 測試覆蓋

**新檔案**: `backend/tests/integration/test_postgres_persistence.py`

測試項目：
- ✅ 缺少 `postgres_url` 應拋出 `ValueError`
- ✅ PostgreSQL 連接失敗應拋出 `RuntimeError`
- ✅ Checkpointer 和 Store 正確初始化
- ✅ 會話可跨實例持久化
- ✅ handlers.py 檢查環境變數
- ✅ 缺少依賴套件錯誤訊息清晰

### 5. 文檔更新

- `docs/BACKEND.md` - 新增 `POSTGRES_URL` 為必填環境變數
- `docs/testing/POSTGRES_PERSISTENCE_VERIFICATION.md` - 完整驗證指南

## 影響範圍

### 修改檔案（共 8 個）

| 檔案 | 變更類型 | 說明 |
|------|---------|------|
| `agent/deep_agent.py` | 重構 | 移除 fallback 邏輯，強制 PostgreSQL |
| `agent/server/handlers.py` | 修改 | 檢查 POSTGRES_URL 環境變數 |
| `agent/server/app.py` | 修改 | 更新 /threads/{id}/history 錯誤處理 |
| `agent/requirements.txt` | 修改 | 標記 PostgreSQL 為必需依賴 |
| `backend/tests/integration/test_postgres_persistence.py` | 新增 | 持久化功能測試 |
| `backend/tests/conftest.py` | 修改 | 新增 PostgreSQL fixtures |
| `docs/BACKEND.md` | 修改 | 更新環境變數說明 |
| `docs/testing/POSTGRES_PERSISTENCE_VERIFICATION.md` | 新增 | 驗證指南 |

### 不相容變更（Breaking Changes）

⚠️ **開發環境需要 PostgreSQL**

- **改造前**: 可以不設定 `POSTGRES_URL`，會使用記憶體模式
- **改造後**: 必須設定 `POSTGRES_URL` 並啟動 PostgreSQL 服務

**遷移步驟**:
```bash
# 1. 啟動 PostgreSQL
docker-compose -f devops/docker-compose.yml up -d postgres

# 2. 設定環境變數
export POSTGRES_URL="postgresql://langgraph:langgraph_secret@localhost:5432/langgraph"

# 3. 驗證連接
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "SELECT 1"
```

## 驗證方法

### 快速驗證

```bash
# 1. 測試 postgres_url 必填
python3 -c "from agent.deep_agent import RefactorAgent; RefactorAgent(postgres_url=None)"
# 預期: ValueError: PostgreSQL URL is required

# 2. 執行持久化測試
pytest backend/tests/integration/test_postgres_persistence.py -v

# 3. 手動測試會話持久化
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test", "thread_id": "test-001"}'

# 重啟容器
docker-compose -f devops/docker-compose.yml restart api

# 查詢歷史（應該能取得之前的對話）
curl http://localhost:8000/threads/test-001/history
```

### 資料庫驗證

```bash
# 檢查表格是否建立
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "\dt"

# 查看 checkpoints 資料
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "
SELECT thread_id, checkpoint_id, created_at
FROM checkpoints
ORDER BY created_at DESC
LIMIT 5;"
```

## 成功標準

✅ **已達成**:
- [x] Agent 初始化時必須連接到 PostgreSQL，失敗則拋出明確錯誤
- [x] 所有冗餘程式碼已移除（SQLite, MemorySaver, InMemoryStore）
- [x] 測試覆蓋關鍵場景（必填檢查、連接失敗、持久化驗證）
- [x] 文檔完整說明環境要求和驗證步驟
- [x] 錯誤訊息清晰易懂，包含排查建議

## 回滾計劃

如需回滾到舊版本（支援 fallback 機制），請執行：

```bash
git revert <commit-hash>
```

或手動恢復以下邏輯：
1. 重新加入 `_setup_memory_persistence()` 方法
2. 在 `_setup_persistence()` 中加入 try-except fallback
3. 恢復 `enable_checkpointing` 和 `checkpoint_db` 參數

## 相關連結

- [LangGraph Checkpointing 官方文檔](https://docs.langchain.com/oss/python/langgraph/add-memory)
- [LangGraph 最佳實踐 (2025)](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025)
- [PostgreSQL 持久化驗證指南](docs/testing/POSTGRES_PERSISTENCE_VERIFICATION.md)
- [Backend 技術文件](docs/BACKEND.md)

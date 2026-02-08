# PostgreSQL 持久化驗證指南

> 本文件說明如何驗證 Agent 會話的 PostgreSQL 持久化功能是否正常運作

**版本**: 1.0
**最後更新**: 2026-02-06

---

## 目錄

1. [背景](#背景)
2. [自動化測試](#自動化測試)
3. [手動驗證](#手動驗證)
4. [資料庫檢查](#資料庫檢查)
5. [問題排查](#問題排查)

---

## 背景

### 為什麼需要 PostgreSQL 持久化？

根據 [LangGraph 官方文檔](https://docs.langchain.com/oss/python/langgraph/add-memory) 和 [最佳實踐指南 (2025)](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025)：

- **生產環境必須使用** PostgresSaver / AsyncPostgresSaver，而非 InMemorySaver
- **持久化優勢**：
  - ✅ 跨容器重啟保留對話狀態
  - ✅ 支援暫停/恢復多輪對話
  - ✅ 可查詢和分析歷史記錄
  - ✅ 支援分散式部署

### 當前架構

```
RefactorAgent (agent/deep_agent.py)
    ↓
PostgresSaver (checkpointer)
    ↓
PostgreSQL Database (langgraph schema)
    ├── checkpoints 表 (會話狀態)
    ├── writes 表 (狀態變更日誌)
    └── store 表 (長期記憶)
```

### 關鍵設計

- **強制使用 PostgreSQL**：開發和生產環境都必須設置 `POSTGRES_URL`
- **失敗即停止**：PostgreSQL 不可用時會拋出明確錯誤，不會 fallback 到記憶體模式
- **自動初始化**：首次使用時會自動呼叫 `.setup()` 建立必要表格

---

## 自動化測試

### 執行完整測試套件

```bash
# 1. 確保 PostgreSQL 正在運行
docker compose -f devops/docker-compose.yml up -d postgres

# 2. 設定環境變數
export POSTGRES_URL="postgresql://langgraph:langgraph_secret@localhost:5432/langgraph"

# 3. 執行持久化測試
pytest backend/tests/integration/test_postgres_persistence.py -v

# 4. 執行完整測試
pytest backend/tests/ -v

# 5. 檢查覆蓋率
pytest backend/tests/ --cov=agent.deep_agent --cov-report=html
open htmlcov/index.html
```

### 測試項目說明

| 測試 | 驗證內容 | 預期結果 |
|------|----------|----------|
| `test_postgres_url_required` | 缺少 POSTGRES_URL 應拋出錯誤 | `ValueError: PostgreSQL URL is required` |
| `test_postgres_connection_failure` | 連接失敗應拋出錯誤 | `RuntimeError: Failed to initialize PostgreSQL` |
| `test_checkpointer_setup` | Checkpointer 正確初始化 | `agent.checkpointer` 和 `agent.store` 不為 None |
| `test_thread_persistence_across_instances` | 跨實例持久化 | 重新建立 Agent 後能取得歷史記錄 |
| `test_environment_variable_check_in_handlers` | handlers.py 檢查環境變數 | 缺少 POSTGRES_URL 時任務標記為 FAILED |
| `test_missing_dependencies_error` | 缺少依賴套件錯誤訊息 | 明確提示安裝指令 |

---

## 手動驗證

### 步驟 1: PostgreSQL 連接測試

```bash
# 啟動 PostgreSQL
docker compose -f devops/docker-compose.yml up -d postgres

# 等待服務就緒
sleep 5

# 驗證連接
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "SELECT version();"
```

**預期輸出**:
```
                                                version
--------------------------------------------------------------------------------------------------------
 PostgreSQL 16.x on x86_64-pc-linux-gnu, compiled by gcc (Debian ...) 12.2.0, 64-bit
(1 row)
```

### 步驟 2: 表格初始化測試

```bash
# 設定環境變數
export POSTGRES_URL="postgresql://langgraph:langgraph_secret@localhost:5432/langgraph"

# 啟動一個 Agent，觸發表格建立
python -c "
import os
from agent.deep_agent import RefactorAgent
from agent.models import AnthropicModelProvider

provider = AnthropicModelProvider()
model = provider.get_model()

agent = RefactorAgent(
    model=model,
    postgres_url=os.environ['POSTGRES_URL']
)
print('✅ Agent 初始化成功')
"
```

**預期輸出**:
```
初始化 PostgreSQL 持久化: postgresql://langgraph:...
✅ PostgresSaver 初始化成功
✅ PostgresStore 初始化成功
✅ Agent 初始化成功
```

**驗證表格**:
```bash
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "\dt"
```

**預期輸出**:
```
                List of relations
 Schema |    Name     | Type  |   Owner
--------+-------------+-------+-----------
 public | checkpoints | table | langgraph
 public | writes      | table | langgraph
 public | store       | table | langgraph
(3 rows)
```

### 步驟 3: 會話持久化測試

**測試目標**: 驗證對話狀態可以跨容器重啟持久化

#### 3.1 發送第一條訊息

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, this is test message 1",
    "thread_id": "test-thread-001"
  }'
```

**預期回應**: 任務已提交（背景執行）

#### 3.2 重啟容器

```bash
docker compose -f devops/docker-compose.yml restart api
```

#### 3.3 發送第二條訊息（應記得之前的對話）

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Do you remember message 1?",
    "thread_id": "test-thread-001"
  }'
```

**驗證**:
```bash
curl -X GET "http://localhost:8000/thread/test-thread-001/history"
```

**預期行為**: Agent 應該能夠參考之前的對話內容回應

### 步驟 4: 錯誤處理測試

#### 4.1 測試：缺少 POSTGRES_URL

```bash
unset POSTGRES_URL

python -c "
from agent.deep_agent import RefactorAgent
from agent.models import AnthropicModelProvider

provider = AnthropicModelProvider()
model = provider.get_model()

try:
    agent = RefactorAgent(model=model, postgres_url=None)
    print('❌ 應該拋出錯誤')
except ValueError as e:
    print(f'✅ 正確拋出 ValueError: {e}')
"
```

**預期輸出**:
```
✅ 正確拋出 ValueError: PostgreSQL URL is required for persistence. Please set POSTGRES_URL environment variable.
```

#### 4.2 測試：無效的 PostgreSQL URL

```bash
export POSTGRES_URL="postgresql://invalid:invalid@localhost:9999/invalid"

python -c "
from agent.deep_agent import RefactorAgent
from agent.models import AnthropicModelProvider

provider = AnthropicModelProvider()
model = provider.get_model()

try:
    agent = RefactorAgent(model=model, postgres_url='postgresql://invalid:invalid@localhost:9999/invalid')
    print('❌ 應該拋出錯誤')
except RuntimeError as e:
    print(f'✅ 正確拋出 RuntimeError: {e}')
"
```

**預期輸出**:
```
❌ PostgreSQL 初始化失敗: ...
✅ 正確拋出 RuntimeError: Failed to initialize PostgreSQL persistence: ... Please check POSTGRES_URL and ensure PostgreSQL is running.
```

---

## 資料庫檢查

### 查看 Checkpoints 表

```bash
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "
SELECT
    thread_id,
    checkpoint_ns,
    checkpoint_id,
    created_at
FROM checkpoints
ORDER BY created_at DESC
LIMIT 10;
"
```

**輸出範例**:
```
      thread_id      | checkpoint_ns |        checkpoint_id         |         created_at
---------------------+---------------+------------------------------+----------------------------
 test-thread-001     | default       | 1ef0... (Base64 UUID v7)     | 2026-02-06 10:23:45.123456
 chat-abc123-...     | default       | 1ef0...                      | 2026-02-06 10:22:30.654321
(2 rows)
```

### 查看 Writes 表

```bash
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "
SELECT
    thread_id,
    task_id,
    idx,
    channel
FROM writes
ORDER BY idx DESC
LIMIT 10;
"
```

### 查看 Store 表

```bash
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "
SELECT
    namespace,
    key,
    created_at,
    updated_at
FROM store
ORDER BY updated_at DESC
LIMIT 10;
"
```

### 清理測試資料（可選）

```bash
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "
-- 清空所有測試相關的 checkpoints
DELETE FROM checkpoints WHERE thread_id LIKE 'test-%';
DELETE FROM writes WHERE thread_id LIKE 'test-%';
"
```

---

## 問題排查

### 問題 1: `POSTGRES_URL not set`

**症狀**:
```
ValueError: PostgreSQL URL is required for persistence. Please set POSTGRES_URL environment variable.
```

**解決方法**:
```bash
# 設定環境變數
export POSTGRES_URL="postgresql://langgraph:langgraph_secret@localhost:5432/langgraph"

# 或在 .env 檔案中設定
echo 'POSTGRES_URL=postgresql://langgraph:langgraph_secret@postgres:5432/langgraph' >> backend/.env
```

### 問題 2: `Failed to initialize PostgreSQL persistence`

**症狀**:
```
RuntimeError: Failed to initialize PostgreSQL persistence: could not connect to server
```

**可能原因**:
1. PostgreSQL 服務未啟動
2. 連線參數錯誤（帳號、密碼、主機、端口）
3. 網路不通（防火牆、Docker 網路）

**檢查步驟**:
```bash
# 1. 確認 PostgreSQL 正在運行
docker ps | grep postgres

# 2. 測試連線
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "SELECT 1"

# 3. 檢查 Docker 網路
docker network inspect refactor-network

# 4. 查看 PostgreSQL 日誌
docker logs refactor-postgres
```

### 問題 3: `relation "checkpoints" does not exist`

**症狀**:
```
psycopg.errors.UndefinedTable: relation "checkpoints" does not exist
```

**原因**: `.setup()` 未被呼叫或執行失敗

**解決方法**:
```python
# 手動建立表格
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string("postgresql://langgraph:langgraph_secret@localhost:5432/langgraph")
checkpointer.setup()  # 建立 checkpoints 和 writes 表
```

### 問題 4: 依賴套件缺失

**症狀**:
```
RuntimeError: PostgreSQL persistence dependencies not installed.
Please run: pip install langgraph-checkpoint-postgres psycopg[binary]
```

**解決方法**:
```bash
cd agent
pip install langgraph-checkpoint-postgres psycopg[binary]
```

### 問題 5: 對話無法跨重啟持久化

**檢查清單**:
- [ ] `POSTGRES_URL` 環境變數正確設定
- [ ] PostgreSQL 服務正常運行
- [ ] `checkpoints` 表已建立且有資料
- [ ] 使用相同的 `thread_id` 發送訊息
- [ ] 沒有手動清空資料庫

**驗證指令**:
```bash
# 檢查是否有 checkpoints 記錄
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "
SELECT COUNT(*) as checkpoint_count FROM checkpoints;
"

# 檢查特定 thread_id
PGPASSWORD=langgraph_secret psql -h localhost -U langgraph -d langgraph -c "
SELECT * FROM checkpoints WHERE thread_id = 'your-thread-id';
"
```

---

## 成功標準

✅ **功能性**:
- [ ] Agent 初始化時必須連接到 PostgreSQL，失敗則拋出明確錯誤
- [ ] 多輪對話可跨容器重啟持久化
- [ ] 所有自動化測試通過

✅ **穩定性**:
- [ ] PostgreSQL 連接失敗時不會靜默降級
- [ ] 錯誤訊息清晰易懂，包含排查建議
- [ ] 資料庫表格自動初始化成功

✅ **可觀測性**:
- [ ] 可透過資料庫查詢驗證對話狀態
- [ ] 日誌清楚顯示持久化狀態（PostgreSQL vs 記憶體）
- [ ] 測試覆蓋率達到 85%+

---

## 相關文檔

- [LangGraph Checkpointing 官方文檔](https://docs.langchain.com/oss/python/langgraph/add-memory)
- [LangGraph Checkpointing 最佳實踐 (2025)](https://sparkco.ai/blog/mastering-langgraph-checkpointing-best-practices-for-2025)
- [langgraph-checkpoint-postgres PyPI](https://pypi.org/project/langgraph-checkpoint-postgres/)
- [Backend 技術文件](../BACKEND.md)
- [測試快速開始指南](QUICK_START.md)

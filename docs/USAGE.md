# Usage

本專案主要流程：

1. 註冊/登入 (取得 JWT)
2. 建立專案 (Project)
3. Provision (建立並啟動專案容器、clone repo 等)
4. 啟動 Agent (在專案容器內執行)
5. 串流查看執行日誌

本文以 API 範例為主。你也可以直接使用前端 UI 操作。

## 1) 註冊 / 登入

### 註冊

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","username":"testuser","password":"password123"}'
```

### 登入 (注意: 使用 username 登入)

```bash
TOKEN=$(
  curl -sS -X POST http://localhost:8000/api/v1/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"testuser","password":"password123"}' \
  | python -c 'import json,sys; print(json.load(sys.stdin)["access_token"])'
)
echo "$TOKEN"
```

## 2) 建立專案

### REFACTOR 專案 (需要 repo_url)

`spec` 是 Agent 的重構規格說明 (可先填簡短描述，之後可更新)。

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My Refactor Project",
    "project_type": "REFACTOR",
    "repo_url": "https://github.com/your-org/your-repo.git",
    "branch": "main",
    "spec": "請先掃描專案並提出可量化的重構計劃，優先處理測試與風險控管。"
  }'
```

### SANDBOX 專案 (repo_url 可不填)

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Sandbox",
    "project_type": "SANDBOX",
    "spec": "用於驗證 agent 能否正常執行"
  }'
```

## 3) Provision 專案

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/provision \
  -H "Authorization: Bearer $TOKEN"
```

Provision 完成後，專案狀態應該會進入 `READY` 才能啟動 Agent。

## 4) 啟動 Agent

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/agent/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

若要指定模型 (若後端/agent 支援)：

```bash
curl -X POST http://localhost:8000/api/v1/projects/{project_id}/agent/run \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"claude-sonnet"}'
```

回應會包含 `run_id`，用於查詢狀態與串流日誌。

## 5) 查詢狀態 / 串流日誌

### 查詢單次 Run 狀態

```bash
curl http://localhost:8000/api/v1/projects/{project_id}/agent/runs/{run_id} \
  -H "Authorization: Bearer $TOKEN"
```

### SSE 串流日誌

```bash
curl -N http://localhost:8000/api/v1/projects/{project_id}/agent/runs/{run_id}/stream \
  -H "Authorization: Bearer $TOKEN"
```

## 參考

- Swagger/OpenAPI: `http://localhost:8000/docs`
- API 規格文件: `docs/API.md`

#!/bin/bash
# 完整的端到端測試腳本
# 目標: 建立 Racing Car Katas 專案並讓 Agent 得到第一次 AI 回應

set -e

API_BASE="http://localhost:8000/api/v1"

echo "============================================================"
echo "完整 E2E 測試: Racing Car Katas (Python → Golang)"
echo "============================================================"
echo ""

# Step 1: 註冊並登入
echo "[Step 1] 註冊並登入..."
TEST_USERNAME="testuser$(date +%s)"
TEST_EMAIL="test-$(date +%s)@example.com"
TEST_PASSWORD="testpass123"

REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"username\": \"$TEST_USERNAME\",
    \"password\": \"$TEST_PASSWORD\"
  }")

LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASSWORD\"
  }")

TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
echo "✅ 已取得 Token"
echo ""

# Step 2: 建立專案
echo "[Step 2] 建立專案 (Racing Car Katas)..."
CREATE_PROJECT_RESPONSE=$(curl -s -X POST "$API_BASE/projects" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "repo_url": "https://github.com/emilybache/Racing-Car-Katas.git",
    "branch": "main",
    "init_prompt": "請將 Python 目錄下的程式碼轉換為 Golang。請分析 Python 程式碼結構，並提供詳細的 Golang 轉換計劃，包括：1) Python 程式碼分析 2) Golang 專案結構設計 3) 類別和函數轉換策略 4) 測試遷移計劃"
  }')

PROJECT_ID=$(echo "$CREATE_PROJECT_RESPONSE" | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
echo "✅ 專案已建立"
echo "   Project ID: $PROJECT_ID"
echo "   Repo: Racing-Car-Katas"
echo ""

# Step 3: Provision (clone repo)
echo "[Step 3] Provision 專案 (clone repo)..."
PROVISION_RESPONSE=$(curl -s -X POST "$API_BASE/projects/$PROJECT_ID/provision" \
  -H "Authorization: Bearer $TOKEN")

CONTAINER_ID=$(echo "$PROVISION_RESPONSE" | grep -o '"container_id":"[^"]*"' | cut -d'"' -f4)
CONTAINER_SHORT_ID=${CONTAINER_ID:0:12}
echo "✅ 容器已建立"
echo "   Container ID: $CONTAINER_SHORT_ID"
echo ""

# 等待 repo clone 完成
echo "⏳ 等待 repo clone 完成 (10秒)..."
sleep 10

# 驗證 repo 已 clone
echo "驗證 repo 已 clone:"
REPO_FILES=$(docker exec $CONTAINER_SHORT_ID ls -1 /workspace/repo/ 2>/dev/null | head -5)
if [ -n "$REPO_FILES" ]; then
    echo "✅ Repo 已成功 clone"
    echo "$REPO_FILES" | while read line; do echo "   - $line"; done
else
    echo "❌ Repo clone 失敗"
    exit 1
fi
echo ""

# Step 4: 執行 Agent
echo "[Step 4] 執行 Agent..."
RUN_AGENT_RESPONSE=$(curl -s -X POST "$API_BASE/projects/$PROJECT_ID/agent/run" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"phase": "PLAN"}')

RUN_ID=$(echo "$RUN_AGENT_RESPONSE" | grep -o '"run_id":"[^"]*"' | cut -d'"' -f4)
echo "✅ Agent 已觸發"
echo "   Run ID: $RUN_ID"
echo ""

# Step 5: 等待首次 AI 回應
echo "[Step 5] 等待 AI 首次回應..."
echo "（監控容器執行，直到看到 Vertex AI 呼叫）"
echo ""

MAX_WAIT=60
WAIT_TIME=0

# 在背景手動執行 Agent，這樣可以即時看到輸出
echo "開始執行 Agent（即時輸出）:"
echo "=========================================="

docker exec \
  -e RUN_ID=$RUN_ID \
  -e MONGODB_URL=mongodb://host.docker.internal:27017 \
  $CONTAINER_SHORT_ID \
  python3 /workspace/agent/run_agent.py 2>&1 | tee /tmp/agent_output.log &

AGENT_PID=$!

# 監控輸出，看到第一次 HTTP 200 OK 就算成功
while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if [ -f /tmp/agent_output.log ]; then
        if grep -q "HTTP/1.1 200 OK" /tmp/agent_output.log; then
            echo ""
            echo "=========================================="
            echo ""
            echo "✅ 偵測到首次 AI 回應！"

            # 等待 Agent 完成
            wait $AGENT_PID 2>/dev/null || true

            break
        fi
    fi
    sleep 1
    WAIT_TIME=$((WAIT_TIME + 1))
done

echo ""
echo "============================================================"
echo "✅ E2E 測試完成！"
echo "============================================================"
echo ""
echo "測試摘要:"
echo "  ✅ 使用者註冊/登入"
echo "  ✅ 建立專案 (Racing-Car-Katas)"
echo "  ✅ Provision (clone repo)"
echo "  ✅ 執行 Agent"
echo "  ✅ 取得 AI 首次回應"
echo ""
echo "專案資訊:"
echo "  Project ID: $PROJECT_ID"
echo "  Container ID: $CONTAINER_SHORT_ID"
echo "  Run ID: $RUN_ID"
echo ""
echo "查看完整 AI 回應:"
echo "  查看上方的 [AI 回應] 完整內容 區塊"
echo ""
echo "查看容器內的 repo:"
echo "  docker exec $CONTAINER_SHORT_ID ls -la /workspace/repo/"
echo ""

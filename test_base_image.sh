#!/bin/bash
# Test Base Image Build and AI Server

set -e

echo "=== Base Image Test ==="

# 1. 建立新的 base image
echo "[1/7] 建立 base image..."
docker build -t refactor-base:latest -f devops/base-image/Dockerfile .

# 2. 驗證目錄結構
echo "[2/7] 驗證目錄結構..."
docker run --rm refactor-base:latest ls -la /workspace/
echo ""

# 3. 驗證 agent 目錄
echo "[3/7] 驗證 agent 目錄..."
docker run --rm refactor-base:latest ls -la /workspace/agent/
echo ""

# 4. 驗證 memory 目錄
echo "[4/7] 驗證 memory 目錄..."
docker run --rm refactor-base:latest ls -la /workspace/memory/
echo ""

# 5. 驗證 AGENTS.md 存在
echo "[5/7] 驗證 AGENTS.md 內容..."
docker run --rm refactor-base:latest sh -c "if [ -f /workspace/memory/AGENTS.md ]; then echo '✅ AGENTS.md exists'; else echo '❌ AGENTS.md missing'; exit 1; fi"
echo ""

# 6. 測試容器啟動和 AI Server
echo "[6/7] 測試 AI Server 啟動..."

# 確保網路存在
docker network create refactor-network 2>/dev/null || true

# 啟動測試容器（需要 ANTHROPIC_API_KEY）
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  警告: ANTHROPIC_API_KEY 未設定，跳過 AI Server 測試"
    echo "如需完整測試，請設定: export ANTHROPIC_API_KEY=sk-ant-..."
else
    docker run -d --name test-ai-server \
      --network refactor-network \
      -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY \
      refactor-base:latest

    # 等待 AI Server 啟動
    echo "等待 AI Server 啟動..."
    sleep 5

    # 7. 測試 health endpoint
    echo "[7/7] 測試 health endpoint..."
    docker run --rm --network refactor-network curlimages/curl:latest \
      curl -f http://test-ai-server:8000/health

    echo ""
    echo "✅ AI Server 正常運行"

    # 清理測試容器
    echo "清理測試容器..."
    docker stop test-ai-server
    docker rm test-ai-server
fi

echo ""
echo "=== Base Image Test Complete ==="

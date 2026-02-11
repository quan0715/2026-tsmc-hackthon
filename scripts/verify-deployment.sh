#!/usr/bin/env bash
# 快速驗證 GCE 部署狀態（以環境變數控制目標）

set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-}"
INSTANCE="${GCE_INSTANCE:-}"
ZONE="${GCE_ZONE:-}"

if [[ -z "$PROJECT_ID" || -z "$INSTANCE" || -z "$ZONE" ]]; then
  echo "Missing required env vars. Example:" >&2
  echo "  export GCP_PROJECT_ID=your-project-id" >&2
  echo "  export GCE_INSTANCE=refactor-agent-prod" >&2
  echo "  export GCE_ZONE=us-central1-a" >&2
  exit 1
fi

echo "Verifying GCE deployment..."

# 檢查容器狀態
echo ""
echo "Container status:"
gcloud compute ssh "$INSTANCE" \
  --zone="$ZONE" \
  --project="$PROJECT_ID" \
  --command="sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

echo ""
echo "Port check:"
gcloud compute ssh "$INSTANCE" \
  --zone="$ZONE" \
  --project="$PROJECT_ID" \
  --command="(command -v ss >/dev/null 2>&1 && sudo ss -tulpn || sudo netstat -tulpn) | grep -E '(5432|27017|8000|80)' || echo 'No port conflicts found'"

echo ""
echo "Health check:"

# 取得外部 IP
EXTERNAL_IP=$(gcloud compute instances describe "$INSTANCE" \
  --zone="$ZONE" \
  --project="$PROJECT_ID" \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "External IP: $EXTERNAL_IP"

# 測試 API (通過 Nginx)
echo -n "API (/api/v1/health via port 80): "
if curl -sf "http://${EXTERNAL_IP}:80/api/v1/health" >/dev/null 2>&1; then
  echo "OK"
else
  echo "FAILED"
fi

# 測試 Frontend
echo -n "Frontend (/ via port 80): "
if curl -sf "http://${EXTERNAL_IP}:80" >/dev/null 2>&1; then
  echo "OK"
else
  echo "FAILED"
fi

echo ""
echo "Done."

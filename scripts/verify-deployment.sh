#!/bin/bash
# 快速驗證 GCE 部署狀態

set -euo pipefail

PROJECT_ID="tsmccareerhack2026-tsid-grp4"
INSTANCE="gce-instance"
ZONE="us-central1-a"

echo "🔍 驗證 GCE 部署狀態..."
echo ""

# 檢查容器狀態
echo "📊 容器狀態："
gcloud compute ssh $INSTANCE \
  --zone=$ZONE \
  --project=$PROJECT_ID \
  --command="sudo docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

echo ""
echo "🔍 端口佔用檢查："
gcloud compute ssh $INSTANCE \
  --zone=$ZONE \
  --project=$PROJECT_ID \
  --command="sudo netstat -tulpn | grep -E '(5432|5433|27017|8000|80)' || echo '無端口衝突'"

echo ""
echo "🏥 健康檢查："

# 取得外部 IP
EXTERNAL_IP=$(gcloud compute instances describe $INSTANCE \
  --zone=$ZONE \
  --project=$PROJECT_ID \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')

echo "外部 IP: $EXTERNAL_IP"

# 測試 API (通過 Nginx)
echo -n "API (/api/v1/health): "
if curl -sf "http://${EXTERNAL_IP}:80/api/v1/health" > /dev/null 2>&1; then
  echo "✅ OK"
else
  echo "❌ FAILED"
fi

# 測試 Frontend
echo -n "Frontend (/): "
if curl -sf "http://${EXTERNAL_IP}:80" > /dev/null 2>&1; then
  echo "✅ OK"
else
  echo "❌ FAILED"
fi

echo ""
echo "✅ 驗證完成"

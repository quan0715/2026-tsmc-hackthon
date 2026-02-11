#!/bin/bash
# 驗證 GitHub Secrets 和 Variables 是否完整設定

set -e

echo "============================================"
echo "🔍 GitHub Secrets & Variables 驗證工具"
echo "============================================"
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 必要的 Secrets
REQUIRED_SECRETS=(
  "GCP_SA_KEY"
)

# 必要的 Variables
REQUIRED_VARIABLES=(
  "REGISTRY_HOST"
  "GCP_PROJECT_ID"
  "GAR_REPOSITORY"
  "GCE_INSTANCE"
  "GCE_ZONE"
  "VITE_API_BASE_URL"
)

# 計數器
SECRETS_OK=0
SECRETS_MISSING=0
VARIABLES_OK=0
VARIABLES_MISSING=0

echo "📋 檢查 GitHub Secrets..."
echo "-------------------------------------------"

# 取得所有 secrets
EXISTING_SECRETS=$(gh secret list 2>/dev/null | awk '{print $1}')

for secret in "${REQUIRED_SECRETS[@]}"; do
  if echo "$EXISTING_SECRETS" | grep -q "^${secret}$"; then
    echo -e "${GREEN}✓${NC} ${secret} - 已設定"
    SECRETS_OK=$((SECRETS_OK + 1))
  else
    echo -e "${RED}✗${NC} ${secret} - ${RED}缺失${NC}"
    SECRETS_MISSING=$((SECRETS_MISSING + 1))
  fi
done

echo ""
echo "📋 檢查 GitHub Variables..."
echo "-------------------------------------------"

# 取得所有 variables
EXISTING_VARIABLES=$(gh variable list 2>/dev/null | awk '{print $1}')

for variable in "${REQUIRED_VARIABLES[@]}"; do
  if echo "$EXISTING_VARIABLES" | grep -q "^${variable}$"; then
    # 取得 variable 的值
    VALUE=$(gh variable get "$variable" 2>/dev/null || echo "無法取得")
    echo -e "${GREEN}✓${NC} ${variable} = ${VALUE}"
    VARIABLES_OK=$((VARIABLES_OK + 1))
  else
    echo -e "${RED}✗${NC} ${variable} - ${RED}缺失${NC}"
    VARIABLES_MISSING=$((VARIABLES_MISSING + 1))
  fi
done

echo ""
echo "============================================"
echo "📊 檢查結果總結"
echo "============================================"

# Secrets 總結
echo ""
echo "Secrets:"
if [ $SECRETS_MISSING -eq 0 ]; then
  echo -e "  ${GREEN}✓ 全部設定完成 (${SECRETS_OK}/${#REQUIRED_SECRETS[@]})${NC}"
else
  echo -e "  ${RED}✗ 缺失 ${SECRETS_MISSING} 個 (${SECRETS_OK}/${#REQUIRED_SECRETS[@]})${NC}"
fi

# Variables 總結
echo ""
echo "Variables:"
if [ $VARIABLES_MISSING -eq 0 ]; then
  echo -e "  ${GREEN}✓ 全部設定完成 (${VARIABLES_OK}/${#REQUIRED_VARIABLES[@]})${NC}"
else
  echo -e "  ${RED}✗ 缺失 ${VARIABLES_MISSING} 個 (${VARIABLES_OK}/${#REQUIRED_VARIABLES[@]})${NC}"
fi

echo ""
echo "============================================"

# 如果有缺失，顯示設定指引
if [ $SECRETS_MISSING -gt 0 ] || [ $VARIABLES_MISSING -gt 0 ]; then
  echo ""
  echo -e "${YELLOW}⚠️  設定指引${NC}"
  echo "-------------------------------------------"

  if [ $SECRETS_MISSING -gt 0 ]; then
    echo ""
    echo "設定缺失的 Secrets:"
    for secret in "${REQUIRED_SECRETS[@]}"; do
      if ! echo "$EXISTING_SECRETS" | grep -q "^${secret}$"; then
        echo "  gh secret set ${secret}"
      fi
    done
  fi

  if [ $VARIABLES_MISSING -gt 0 ]; then
    echo ""
    echo "設定缺失的 Variables:"
    for variable in "${REQUIRED_VARIABLES[@]}"; do
      if ! echo "$EXISTING_VARIABLES" | grep -q "^${variable}$"; then
        case "$variable" in
          "REGISTRY_HOST")
            echo "  gh variable set ${variable} --body \"us-central1-docker.pkg.dev\""
            ;;
          "GCP_PROJECT_ID")
            echo "  gh variable set ${variable} --body \"your-project-id\""
            ;;
          "GAR_REPOSITORY")
            echo "  gh variable set ${variable} --body \"images\""
            ;;
          "GCE_INSTANCE")
            echo "  gh variable set ${variable} --body \"refactor-agent-prod\""
            ;;
          "GCE_ZONE")
            echo "  gh variable set ${variable} --body \"us-central1-a\""
            ;;
          "VITE_API_BASE_URL")
            echo "  gh variable set ${variable} --body \"http://your-instance-ip:8000\""
            ;;
          *)
            echo "  gh variable set ${variable} --body \"<value>\""
            ;;
        esac
      fi
    done
  fi

  echo ""
  echo "詳細設定說明請參考: .github/workflows/GCE_DEPLOY.md"
  echo ""

  exit 1
else
  echo ""
  echo -e "${GREEN}✅ 所有必要的 Secrets 和 Variables 都已正確設定！${NC}"
  echo ""
  echo "🚀 你可以開始使用 GitHub Actions 進行部署了"
  echo ""
  exit 0
fi

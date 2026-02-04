#!/usr/bin/env bash

# Auto-Refactor-Agent 認證管理腳本
# 註冊新用戶或登入現有用戶以獲取 JWT token

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 預設值
MODE=""
EMAIL=""
USERNAME=""
PASSWORD=""
API_URL="http://localhost:8000"
TOKEN_FILE=".token"

# 解析參數
while [[ $# -gt 0 ]]; do
  case $1 in
    --register)
      MODE="register"
      shift
      ;;
    --login)
      MODE="login"
      shift
      ;;
    --email)
      EMAIL="$2"
      shift 2
      ;;
    --username)
      USERNAME="$2"
      shift 2
      ;;
    --password)
      PASSWORD="$2"
      shift 2
      ;;
    --api-url)
      API_URL="$2"
      shift 2
      ;;
    --token-file)
      TOKEN_FILE="$2"
      shift 2
      ;;
    --help|-h)
      echo "使用方式: $0 [選項]"
      echo ""
      echo "模式選項 (必選其一):"
      echo "  --register           註冊新用戶"
      echo "  --login              登入現有用戶"
      echo ""
      echo "認證參數:"
      echo "  --email EMAIL        使用者 email"
      echo "  --username USERNAME  使用者名稱 (註冊時需要)"
      echo "  --password PASSWORD  密碼"
      echo ""
      echo "其他選項:"
      echo "  --api-url URL        API 基礎 URL (預設: http://localhost:8000)"
      echo "  --token-file FILE    Token 儲存路徑 (預設: .token)"
      echo "  --help, -h           顯示此幫助訊息"
      echo ""
      echo "範例:"
      echo "  # 註冊新用戶（互動式）"
      echo "  $0 --register"
      echo ""
      echo "  # 註冊新用戶（非互動式）"
      echo "  $0 --register --email user@example.com --username myuser --password mypass123"
      echo ""
      echo "  # 登入現有用戶（互動式）"
      echo "  $0 --login"
      echo ""
      echo "  # 登入現有用戶（非互動式）"
      echo "  $0 --login --email user@example.com --password mypass123"
      exit 0
      ;;
    *)
      echo -e "${RED}未知選項: $1${NC}"
      echo "使用 --help 查看幫助"
      exit 1
      ;;
  esac
done

# 檢查模式
if [ -z "$MODE" ]; then
  echo -e "${RED}錯誤: 必須指定 --register 或 --login${NC}"
  echo "使用 --help 查看幫助"
  exit 1
fi

# 輸出函數
print_success() {
  echo -e "${GREEN}✓${NC} $1"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
}

print_info() {
  echo -e "${BLUE}ℹ${NC} $1"
}

# 驗證 email 格式
validate_email() {
  local email=$1
  if [[ ! "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
    print_error "無效的 email 格式: $email"
    return 1
  fi
  return 0
}

# 互動式輸入
prompt_email() {
  if [ -z "$EMAIL" ]; then
    read -p "Email: " EMAIL
  fi
  validate_email "$EMAIL" || exit 1
}

prompt_username() {
  if [ -z "$USERNAME" ]; then
    read -p "Username: " USERNAME
  fi
  if [ -z "$USERNAME" ]; then
    print_error "Username 不能為空"
    exit 1
  fi
}

prompt_password() {
  if [ -z "$PASSWORD" ]; then
    read -s -p "Password: " PASSWORD
    echo ""
  fi
  if [ -z "$PASSWORD" ]; then
    print_error "Password 不能為空"
    exit 1
  fi
}

# 儲存 token
save_token() {
  local token=$1
  local email=$2
  local expires=$3

  # 建立 token 檔案
  cat > "$TOKEN_FILE" <<EOF
# Auto-generated JWT token for Auto-Refactor-Agent
# Generated at: $(date '+%Y-%m-%d %H:%M:%S')
# User: $email
# Expires in: $expires seconds ($(($expires / 3600)) hours)
$token
EOF

  # 設定檔案權限為 600
  chmod 600 "$TOKEN_FILE"

  print_success "Token 已儲存到: $TOKEN_FILE"
  print_info "Token 將在 $(($expires / 3600)) 小時後過期"
}

# 註冊用戶
register_user() {
  local email=$1
  local username=$2
  local password=$3
  local api_url=$4

  print_info "正在註冊用戶..."

  # 清理參數避免注入攻擊
  email=$(echo "$email" | sed 's/[^a-zA-Z0-9@._+-]//g')
  username=$(echo "$username" | sed 's/[^a-zA-Z0-9_-]//g')

  RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${api_url}/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$email\",\"username\":\"$username\",\"password\":\"$password\"}" 2>&1)

  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  BODY=$(echo "$RESPONSE" | head -n -1)

  if [ "$HTTP_CODE" = "201" ]; then
    print_success "用戶註冊成功"

    # 解析回應
    if command -v jq >/dev/null 2>&1; then
      USER_ID=$(echo "$BODY" | jq -r '.id // "unknown"')
      USER_EMAIL=$(echo "$BODY" | jq -r '.email // "unknown"')
      print_info "User ID: $USER_ID"
      print_info "Email: $USER_EMAIL"
    fi

    # 自動登入
    print_info "正在自動登入..."
    login_user "$email" "$password" "$api_url"
  else
    print_error "註冊失敗 (HTTP $HTTP_CODE)"

    if command -v jq >/dev/null 2>&1; then
      ERROR=$(echo "$BODY" | jq -r '.detail // "Unknown error"')
      echo "  錯誤: $ERROR"
    else
      echo "  回應: $BODY"
    fi

    return 1
  fi
}

# 登入用戶
login_user() {
  local email=$1
  local password=$2
  local api_url=$3

  print_info "正在登入..."

  # 清理 email 參數
  email=$(echo "$email" | sed 's/[^a-zA-Z0-9@._+-]//g')

  RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "${api_url}/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$email\",\"password\":\"$password\"}" 2>&1)

  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  BODY=$(echo "$RESPONSE" | head -n -1)

  if [ "$HTTP_CODE" = "200" ]; then
    print_success "登入成功"

    # 解析 token
    if command -v jq >/dev/null 2>&1; then
      TOKEN=$(echo "$BODY" | jq -r '.access_token')
      EXPIRES=$(echo "$BODY" | jq -r '.expires_in')

      if [ "$TOKEN" != "null" ] && [ -n "$TOKEN" ]; then
        save_token "$TOKEN" "$email" "$EXPIRES"

        # 驗證 token
        verify_token "$TOKEN" "$api_url"
      else
        print_error "無法解析 token"
        return 1
      fi
    else
      print_error "需要安裝 jq 來解析 JSON 回應"
      echo "  macOS: brew install jq"
      echo "  Ubuntu: sudo apt-get install jq"
      return 1
    fi
  else
    print_error "登入失敗 (HTTP $HTTP_CODE)"

    if command -v jq >/dev/null 2>&1; then
      ERROR=$(echo "$BODY" | jq -r '.detail // "Unknown error"')
      echo "  錯誤: $ERROR"
    else
      echo "  回應: $BODY"
    fi

    return 1
  fi
}

# 驗證 token
verify_token() {
  local token=$1
  local api_url=$2

  print_info "驗證 token..."

  RESPONSE=$(curl -s -w "\n%{http_code}" -X GET "${api_url}/api/v1/auth/me" \
    -H "Authorization: Bearer $token" 2>&1)

  HTTP_CODE=$(echo "$RESPONSE" | tail -1)
  BODY=$(echo "$RESPONSE" | head -n -1)

  if [ "$HTTP_CODE" = "200" ]; then
    print_success "Token 有效"

    if command -v jq >/dev/null 2>&1; then
      USER_NAME=$(echo "$BODY" | jq -r '.username // "unknown"')
      USER_EMAIL=$(echo "$BODY" | jq -r '.email // "unknown"')
      IS_ACTIVE=$(echo "$BODY" | jq -r '.is_active // false')

      echo ""
      echo "═══════════════════════════════════════════"
      echo "使用者資訊:"
      echo "  Username: $USER_NAME"
      echo "  Email: $USER_EMAIL"
      echo "  Active: $IS_ACTIVE"
      echo "═══════════════════════════════════════════"
    fi
  else
    print_error "Token 驗證失敗 (HTTP $HTTP_CODE)"
    return 1
  fi
}

# 檢查依賴
check_dependencies() {
  if ! command -v curl >/dev/null 2>&1; then
    print_error "需要安裝 curl"
    exit 1
  fi

  if ! command -v jq >/dev/null 2>&1; then
    print_error "需要安裝 jq"
    echo "  macOS: brew install jq"
    echo "  Ubuntu: sudo apt-get install jq"
    exit 1
  fi
}

# 主執行流程
main() {
  echo "╔════════════════════════════════════════════════════════╗"
  echo "║   Auto-Refactor-Agent 認證管理                          ║"
  echo "╚════════════════════════════════════════════════════════╝"
  echo ""

  # 檢查依賴
  check_dependencies

  # 檢查 API 可用性
  if ! curl -sf "${API_URL}/api/v1/health" >/dev/null 2>&1; then
    print_error "無法連線到 API: $API_URL"
    echo "  請確認 API 服務正在運行"
    echo "  執行: ./scripts/check-env.sh"
    exit 1
  fi

  # 執行對應模式
  if [ "$MODE" = "register" ]; then
    echo -e "${BLUE}模式: 註冊新用戶${NC}"
    echo ""

    prompt_email
    prompt_username
    prompt_password

    register_user "$EMAIL" "$USERNAME" "$PASSWORD" "$API_URL"

  elif [ "$MODE" = "login" ]; then
    echo -e "${BLUE}模式: 登入現有用戶${NC}"
    echo ""

    prompt_email
    prompt_password

    login_user "$EMAIL" "$PASSWORD" "$API_URL"
  fi

  echo ""
  print_success "完成！"
  echo ""
  echo "使用 token 呼叫 API:"
  echo "  export TOKEN=\$(cat $TOKEN_FILE | tail -1)"
  echo "  curl -H \"Authorization: Bearer \$TOKEN\" ${API_URL}/api/v1/auth/me"
}

# 執行主函數
main

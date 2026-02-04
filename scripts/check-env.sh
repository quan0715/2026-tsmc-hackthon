#!/usr/bin/env bash

# Auto-Refactor-Agent 環境驗證腳本
# 檢查 Docker、MongoDB、API、Frontend 服務以及環境變數

set -e

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 計數器
SUCCESS_COUNT=0
ERROR_COUNT=0
WARNING_COUNT=0

# 詳細模式
VERBOSE=false

# 解析參數
while [[ $# -gt 0 ]]; do
  case $1 in
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      echo "使用方式: $0 [選項]"
      echo ""
      echo "選項:"
      echo "  --verbose, -v    顯示詳細資訊"
      echo "  --help, -h       顯示此幫助訊息"
      echo ""
      echo "檢查項目:"
      echo "  - Docker daemon 運行狀態"
      echo "  - Base image 存在性"
      echo "  - Docker network 存在性"
      echo "  - MongoDB 容器和連線"
      echo "  - API 服務和 health endpoint"
      echo "  - Frontend 服務"
      echo "  - 環境變數設定"
      exit 0
      ;;
    *)
      echo "未知選項: $1"
      echo "使用 --help 查看幫助"
      exit 1
      ;;
  esac
done

# 輸出函數
print_success() {
  echo -e "${GREEN}✓${NC} $1"
  ((SUCCESS_COUNT++))
}

print_error() {
  echo -e "${RED}✗${NC} $1"
  ((ERROR_COUNT++))
}

print_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
  ((WARNING_COUNT++))
}

print_info() {
  if [ "$VERBOSE" = true ]; then
    echo -e "  $1"
  fi
}

print_fix() {
  echo -e "  ${YELLOW}修復:${NC} $1"
}

# 檢查函數
check_docker_daemon() {
  echo ""
  echo "=== Docker 檢查 ==="

  if docker info >/dev/null 2>&1; then
    print_success "Docker daemon 運行中"
    print_info "$(docker version --format 'Docker version: {{.Server.Version}}')"
  else
    print_error "Docker daemon 未運行"
    print_fix "啟動 Docker Desktop 或執行 'sudo systemctl start docker'"
    return 1
  fi
}

check_base_image() {
  if docker images --format '{{.Repository}}:{{.Tag}}' | grep -q '^refactor-base:latest$'; then
    print_success "Base image 'refactor-base:latest' 存在"
    IMAGE_INFO=$(docker images refactor-base:latest --format '{{.Size}} | {{.CreatedAt}}' | head -1)
    print_info "Size: $(echo $IMAGE_INFO | cut -d'|' -f1 | xargs) | Created: $(echo $IMAGE_INFO | cut -d'|' -f2 | xargs)"
  else
    print_error "Base image 'refactor-base:latest' 不存在"
    print_fix "執行: docker build -t refactor-base:latest -f devops/base-image/Dockerfile ."
    return 1
  fi
}

check_docker_network() {
  if docker network ls --format '{{.Name}}' | grep -q '^refactor-network$'; then
    print_success "Docker network 'refactor-network' 存在"
  else
    print_warning "Docker network 'refactor-network' 不存在"
    print_fix "執行: docker-compose -f devops/docker-compose.yml up -d"
  fi
}

check_mongodb_container() {
  echo ""
  echo "=== MongoDB 檢查 ==="

  if docker ps --filter "name=refactor-mongodb" --format '{{.Names}}' | grep -q 'refactor-mongodb'; then
    print_success "MongoDB 容器 'refactor-mongodb' 運行中"

    # 檢查 MongoDB 連線
    if docker exec refactor-mongodb mongosh --quiet --eval "db.adminCommand('ping')" >/dev/null 2>&1; then
      print_success "MongoDB 連線測試通過"
    else
      print_error "MongoDB 連線測試失敗"
      print_fix "檢查容器日誌: docker logs refactor-mongodb"
      return 1
    fi
  else
    print_error "MongoDB 容器 'refactor-mongodb' 未運行"
    print_fix "執行: docker-compose -f devops/docker-compose.yml up -d mongodb"
    return 1
  fi
}

check_api_container() {
  echo ""
  echo "=== API 服務檢查 ==="

  if docker ps --filter "name=refactor-api" --format '{{.Names}}' | grep -q 'refactor-api'; then
    print_success "API 容器 'refactor-api' 運行中"

    # 等待 API 啟動
    sleep 2

    # 檢查 health endpoint
    HEALTH_RESPONSE=$(curl -s -w "\n%{http_code}" http://localhost:8000/api/v1/health 2>/dev/null || echo -e "\n000")
    HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -1)
    BODY=$(echo "$HEALTH_RESPONSE" | head -n -1)

    if [ "$HTTP_CODE" = "200" ]; then
      print_success "API health endpoint 回應正常"

      # 解析 JSON 回應
      if command -v jq >/dev/null 2>&1; then
        STATUS=$(echo "$BODY" | jq -r '.status // "unknown"')
        DB_STATUS=$(echo "$BODY" | jq -r '.database // "unknown"')
        print_info "Status: $STATUS | Database: $DB_STATUS"
      else
        print_info "Response: $BODY"
      fi
    else
      print_error "API health endpoint 無回應 (HTTP $HTTP_CODE)"
      print_fix "檢查容器日誌: docker logs refactor-api"
      return 1
    fi
  else
    print_error "API 容器 'refactor-api' 未運行"
    print_fix "執行: docker-compose -f devops/docker-compose.yml up -d api"
    return 1
  fi
}

check_frontend_container() {
  echo ""
  echo "=== Frontend 服務檢查 ==="

  if docker ps --filter "name=refactor-frontend" --format '{{.Names}}' | grep -q 'refactor-frontend'; then
    print_success "Frontend 容器 'refactor-frontend' 運行中"

    # 檢查 port 5173 可訪問性
    if curl -s http://localhost:5173 >/dev/null 2>&1; then
      print_success "Frontend port 5173 可訪問"
    else
      print_warning "Frontend port 5173 無回應（可能仍在啟動中）"
    fi
  else
    print_error "Frontend 容器 'refactor-frontend' 未運行"
    print_fix "執行: docker-compose -f devops/docker-compose.yml up -d frontend"
    return 1
  fi
}

check_env_file() {
  echo ""
  echo "=== 環境變數檢查 ==="

  ENV_FILE="backend/.env"

  if [ -f "$ENV_FILE" ]; then
    print_success "環境檔案 '$ENV_FILE' 存在"

    # 檢查必要變數
    source "$ENV_FILE"

    # ANTHROPIC_API_KEY
    if [ -n "$ANTHROPIC_API_KEY" ] && [ "$ANTHROPIC_API_KEY" != "your-anthropic-api-key-here" ]; then
      print_success "ANTHROPIC_API_KEY 已設定"
      print_info "Length: ${#ANTHROPIC_API_KEY} characters"
    else
      print_error "ANTHROPIC_API_KEY 未設定或為預設值"
      print_fix "編輯 $ENV_FILE 並設定有效的 API key"
    fi

    # JWT_SECRET_KEY
    if [ -n "$JWT_SECRET_KEY" ] && [ "$JWT_SECRET_KEY" != "your-super-secret-jwt-key-change-this-in-production" ]; then
      print_success "JWT_SECRET_KEY 已設定"
    else
      print_warning "JWT_SECRET_KEY 使用預設值（不安全）"
      print_fix "生產環境請更換: openssl rand -hex 32"
    fi

    # MONGODB_URL
    if [ -n "$MONGODB_URL" ]; then
      print_success "MONGODB_URL 已設定"
      print_info "URL: $MONGODB_URL"
    else
      print_error "MONGODB_URL 未設定"
    fi

  else
    print_error "環境檔案 '$ENV_FILE' 不存在"
    print_fix "複製範本: cp backend/.env.example backend/.env"
    return 1
  fi
}

check_dependencies() {
  echo ""
  echo "=== 依賴項檢查 ==="

  # 檢查 jq
  if command -v jq >/dev/null 2>&1; then
    print_success "jq 已安裝 ($(jq --version))"
  else
    print_warning "jq 未安裝（建議安裝以解析 JSON）"
    print_fix "macOS: brew install jq | Ubuntu: sudo apt-get install jq"
  fi

  # 檢查 curl
  if command -v curl >/dev/null 2>&1; then
    print_success "curl 已安裝"
  else
    print_error "curl 未安裝"
  fi

  # 檢查 docker-compose
  if command -v docker-compose >/dev/null 2>&1; then
    print_success "docker-compose 已安裝 ($(docker-compose --version))"
  else
    print_error "docker-compose 未安裝"
  fi
}

# 主執行流程
main() {
  echo "╔════════════════════════════════════════════════════════╗"
  echo "║   Auto-Refactor-Agent 環境驗證                          ║"
  echo "╚════════════════════════════════════════════════════════╝"

  # 執行所有檢查
  check_dependencies
  check_docker_daemon || true
  check_base_image || true
  check_docker_network || true
  check_mongodb_container || true
  check_api_container || true
  check_frontend_container || true
  check_env_file || true

  # 顯示統計摘要
  echo ""
  echo "════════════════════════════════════════════════════════"
  echo "檢查摘要:"
  echo -e "  ${GREEN}✓ 成功: $SUCCESS_COUNT${NC}"
  echo -e "  ${RED}✗ 錯誤: $ERROR_COUNT${NC}"
  echo -e "  ${YELLOW}⚠ 警告: $WARNING_COUNT${NC}"
  echo "════════════════════════════════════════════════════════"

  if [ $ERROR_COUNT -gt 0 ]; then
    echo ""
    echo -e "${RED}環境檢查失敗，請修復上述錯誤後重試。${NC}"
    exit 1
  elif [ $WARNING_COUNT -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}環境檢查通過，但存在警告項目。${NC}"
    exit 0
  else
    echo ""
    echo -e "${GREEN}✓ 所有檢查通過！環境就緒。${NC}"
    exit 0
  fi
}

# 執行主函數
main

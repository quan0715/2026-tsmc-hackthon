#!/bin/bash

# 測試執行腳本
# 用法: ./scripts/run_tests.sh [選項]
#
# 選項:
#   all         - 執行所有測試 (預設)
#   unit        - 只執行單元測試
#   integration - 只執行整合測試
#   e2e         - 只執行端到端測試
#   coverage    - 執行測試並生成覆蓋率報告
#   watch       - 監視模式（檔案變更時自動執行）
#   clean       - 清理測試資料庫

set -e  # 遇到錯誤立即退出

# 顏色輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 切換到 backend 目錄
cd "$(dirname "$0")/.."

# 檢查 MongoDB 是否運行
check_mongodb() {
    echo -e "${YELLOW}檢查 MongoDB 連接...${NC}"
    if ! docker ps | grep -q mongodb; then
        echo -e "${RED}MongoDB 未運行！${NC}"
        echo -e "${YELLOW}嘗試啟動 MongoDB...${NC}"
        docker start mongodb 2>/dev/null || docker run -d --name mongodb -p 27017:27017 mongo:7
        sleep 2
    fi
    echo -e "${GREEN}✓ MongoDB 運行中${NC}"
}

# 清理測試資料庫
clean_db() {
    echo -e "${YELLOW}清理測試資料庫...${NC}"
    docker exec mongodb mongosh refactor_agent_test --eval "db.dropDatabase()" 2>/dev/null || true
    echo -e "${GREEN}✓ 測試資料庫已清理${NC}"
}

# 執行測試
run_tests() {
    local test_path=$1
    local description=$2

    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}執行 ${description}${NC}"
    echo -e "${GREEN}========================================${NC}"

    python3 -m pytest "${test_path}" -v --tb=short

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ ${description} 通過！${NC}"
    else
        echo -e "${RED}✗ ${description} 失敗！${NC}"
        exit $exit_code
    fi
}

# 執行覆蓋率測試
run_coverage() {
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}執行測試並生成覆蓋率報告${NC}"
    echo -e "${GREEN}========================================${NC}"

    python3 -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing --cov-report=term:skip-covered -v

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo -e "${GREEN}✓ 測試通過！${NC}"
        echo -e "${YELLOW}覆蓋率報告已生成: htmlcov/index.html${NC}"

        # 嘗試開啟報告
        if command -v open &> /dev/null; then
            open htmlcov/index.html
        elif command -v xdg-open &> /dev/null; then
            xdg-open htmlcov/index.html
        fi
    else
        echo -e "${RED}✗ 測試失敗！${NC}"
        exit $exit_code
    fi
}

# 監視模式
watch_tests() {
    echo -e "${YELLOW}監視模式啟動（按 Ctrl+C 退出）${NC}"

    if ! command -v pytest-watch &> /dev/null; then
        echo -e "${YELLOW}安裝 pytest-watch...${NC}"
        pip install pytest-watch
    fi

    ptw tests/ -- -v --tb=short
}

# 主程式
main() {
    local mode=${1:-all}

    # 檢查 MongoDB
    check_mongodb

    case "$mode" in
        all)
            run_tests "tests/" "所有測試"
            ;;
        unit)
            run_tests "tests/unit/" "單元測試"
            ;;
        integration)
            run_tests "tests/integration/" "整合測試"
            ;;
        e2e)
            run_tests "tests/e2e/" "端到端測試"
            ;;
        coverage)
            run_coverage
            ;;
        watch)
            watch_tests
            ;;
        clean)
            clean_db
            ;;
        *)
            echo "用法: $0 [all|unit|integration|e2e|coverage|watch|clean]"
            echo ""
            echo "選項:"
            echo "  all         - 執行所有測試 (預設)"
            echo "  unit        - 只執行單元測試"
            echo "  integration - 只執行整合測試"
            echo "  e2e         - 只執行端到端測試"
            echo "  coverage    - 執行測試並生成覆蓋率報告"
            echo "  watch       - 監視模式（檔案變更時自動執行）"
            echo "  clean       - 清理測試資料庫"
            exit 1
            ;;
    esac

    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
}

# 執行主程式
main "$@"

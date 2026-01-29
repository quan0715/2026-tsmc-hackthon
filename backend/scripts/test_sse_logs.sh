#!/bin/bash
# SSE 日誌串流測試腳本

PROJECT_ID=$1

if [ -z "$PROJECT_ID" ]; then
    echo "用法: $0 <project_id>"
    exit 1
fi

echo "=== 測試 SSE 日誌串流 ==="
echo "專案 ID: $PROJECT_ID"
echo ""

echo "1. 測試不 follow (只取最後 10 行)"
curl -N "http://localhost:8000/api/v1/projects/$PROJECT_ID/logs/stream?follow=false&tail=10"

echo ""
echo ""
echo "2. 測試 follow 模式 (按 Ctrl+C 停止)"
echo "   這將持續串流容器的日誌輸出..."
curl -N "http://localhost:8000/api/v1/projects/$PROJECT_ID/logs/stream?follow=true&tail=5"

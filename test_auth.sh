#!/bin/bash

# 測試認證 API
BASE_URL="http://localhost:8000"

echo "========================================="
echo "測試用戶註冊"
echo "========================================="

# 註冊新用戶
REGISTER_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "password123"
  }')

echo "註冊回應:"
echo "$REGISTER_RESPONSE" | jq '.' 2>/dev/null || echo "$REGISTER_RESPONSE"

echo ""
echo "========================================="
echo "測試用戶登入"
echo "========================================="

# 登入
LOGIN_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "password123"
  }')

echo "登入回應:"
echo "$LOGIN_RESPONSE" | jq '.' 2>/dev/null || echo "$LOGIN_RESPONSE"

# 提取 token
TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token' 2>/dev/null)

if [ "$TOKEN" != "null" ] && [ ! -z "$TOKEN" ]; then
  echo ""
  echo "========================================="
  echo "登入成功！Token:"
  echo "$TOKEN"
  echo "========================================="

  echo ""
  echo "測試認證 API (獲取當前用戶資訊):"
  curl -s -X GET "${BASE_URL}/api/v1/auth/me" \
    -H "Authorization: Bearer $TOKEN" | jq '.' 2>/dev/null
else
  echo ""
  echo "登入失敗，請檢查錯誤訊息"
fi

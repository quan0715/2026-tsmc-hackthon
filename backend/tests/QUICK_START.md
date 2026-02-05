# 測試快速入門指南

## 前置準備

### 1. 確認 MongoDB 運行中
```bash
# 啟動 MongoDB (使用 Docker)
docker run -d --name mongodb -p 27017:27017 mongo:7

# 或使用現有的 docker-compose
docker-compose -f devops/docker-compose.yml up -d mongodb
```

### 2. 安裝測試依賴
```bash
cd backend
pip install -r requirements.txt
```

必要的測試套件：
- `pytest`
- `pytest-asyncio`
- `httpx`
- `pymongo>=4.13.0` (MongoDB async driver)

## 執行測試

### 快速執行所有測試
```bash
cd backend
python3 -m pytest tests/ -v
```

### 執行特定測試層級

#### 單元測試（最快）
```bash
pytest tests/unit/ -v
```

#### 整合測試
```bash
pytest tests/integration/ -v
```

#### 端到端測試
```bash
pytest tests/e2e/ -v
```

### 執行特定測試檔案

```bash
# 認證測試
pytest tests/integration/test_auth_api.py -v

# 聊天測試
pytest tests/integration/test_chat_api.py -v

# 容器服務測試
pytest tests/unit/test_container_service.py -v
```

### 執行特定測試函數

```bash
# 使用完整路徑
pytest tests/integration/test_auth_api.py::TestRegisterAPI::test_register_success -v

# 使用 -k 過濾
pytest tests/ -k "test_register" -v
```

## 測試覆蓋率

### 生成覆蓋率報告

```bash
# HTML 報告
pytest tests/ --cov=app --cov-report=html --cov-report=term

# 開啟報告
open htmlcov/index.html  # macOS
# xdg-open htmlcov/index.html  # Linux
# start htmlcov/index.html  # Windows
```

### 只看特定模組的覆蓋率

```bash
# 只測試 auth 模組
pytest tests/ --cov=app.services.auth_service --cov-report=term

# 只測試 routers
pytest tests/ --cov=app.routers --cov-report=term
```

## 提高測試速度

### 並行執行測試

```bash
# 安裝 pytest-xdist
pip install pytest-xdist

# 自動使用所有 CPU 核心
pytest tests/ -n auto

# 指定核心數量
pytest tests/ -n 4
```

### 只執行失敗的測試

```bash
# 第一次執行
pytest tests/ --lf  # last-failed

# 或執行失敗的測試後再執行其他
pytest tests/ --ff  # failed-first
```

### 停在第一個失敗

```bash
pytest tests/ -x  # stop on first failure
```

## 常見問題排查

### 問題 1: ImportError 或 ModuleNotFoundError

**原因**: Python 路徑問題

**解決方案**:
```bash
# 確保在 backend 目錄執行
cd /Users/quan/auto-refactor-agent/backend
export PYTHONPATH=$PYTHONPATH:$(pwd)
pytest tests/ -v
```

### 問題 2: MongoDB 連接失敗

**錯誤訊息**: `pymongo.errors.ServerSelectionTimeoutError`

**解決方案**:
```bash
# 檢查 MongoDB 是否運行
docker ps | grep mongo

# 如果沒有運行，啟動它
docker start mongodb
# 或
docker run -d --name mongodb -p 27017:27017 mongo:7
```

### 問題 3: 測試資料庫沒有清理

**現象**: 測試失敗，錯誤提示資料已存在

**解決方案**:
```bash
# 手動清理測試資料庫
docker exec -it mongodb mongosh refactor_agent_test --eval "db.dropDatabase()"

# 或在 Python 中
python3 -c "
from pymongo import AsyncMongoClient
import asyncio
async def cleanup():
    client = AsyncMongoClient('mongodb://localhost:27017')
    await client.drop_database('refactor_agent_test')
    await client.close()
asyncio.run(cleanup())
"
```

### 問題 4: Fixture 找不到

**錯誤訊息**: `fixture 'xxx' not found`

**原因**: pytest 沒有載入 conftest.py

**解決方案**:
```bash
# 確認 conftest.py 存在
ls tests/conftest.py

# 確認測試檔案在正確位置
ls tests/unit/
ls tests/integration/

# 執行時加上 -v 查看載入的 fixtures
pytest tests/unit/test_auth_service.py -v --fixtures
```

### 問題 5: Mock 沒有生效

**原因**: monkeypatch 路徑錯誤

**檢查**:
- 確認 mock 的是實際被呼叫的模組路徑
- 使用 `from ... import ...` 時，要 mock import 的位置

**範例**:
```python
# 如果程式碼是
# from app.services.container_service import ContainerService
# service = ContainerService()

# 則應該 mock
monkeypatch.setattr("app.services.container_service.subprocess.run", mock_run)

# 而不是
monkeypatch.setattr("subprocess.run", mock_run)  # ❌ 錯誤
```

## 測試開發流程

### 1. 新增測試的步驟

```bash
# 1. 確定測試類型
# - 測試業務邏輯 → unit/
# - 測試 API 端點 → integration/
# - 測試完整流程 → e2e/

# 2. 建立測試檔案
touch tests/unit/test_new_service.py

# 3. 引入必要的 fixtures
# 在測試函數參數中加入需要的 fixtures

# 4. 撰寫測試
# 使用 arrange-act-assert 模式

# 5. 執行測試
pytest tests/unit/test_new_service.py -v

# 6. 檢查覆蓋率
pytest tests/unit/test_new_service.py --cov=app.services.new_service
```

### 2. TDD 開發流程

```bash
# Red: 寫一個會失敗的測試
pytest tests/unit/test_feature.py -v

# Green: 寫最少的程式碼讓測試通過
# (修改 app/services/...)

pytest tests/unit/test_feature.py -v

# Refactor: 重構程式碼
# (優化 app/services/...)

pytest tests/unit/test_feature.py -v
```

## 測試撰寫建議

### 好的測試名稱

```python
# ✅ 好的命名
def test_create_user_with_valid_email_succeeds():
def test_login_with_wrong_password_returns_401():
def test_list_projects_returns_only_owned_projects():

# ❌ 不好的命名
def test_user():
def test_case_1():
def test_function():
```

### 使用 Arrange-Act-Assert 模式

```python
@pytest.mark.asyncio
async def test_create_project(auth_client, test_user):
    # Arrange: 準備測試資料
    project_data = {
        "repo_url": "https://github.com/test/repo.git",
        "branch": "main",
        "spec": "Test project"
    }

    # Act: 執行操作
    response = await auth_client.post("/api/v1/projects", json=project_data)

    # Assert: 驗證結果
    assert response.status_code == 201
    assert response.json()["repo_url"] == project_data["repo_url"]
```

### 一個測試只驗證一件事

```python
# ✅ 好的做法
def test_create_project_returns_201():
    response = await auth_client.post(...)
    assert response.status_code == 201

def test_create_project_returns_correct_data():
    response = await auth_client.post(...)
    assert response.json()["repo_url"] == expected_url

# ❌ 避免
def test_create_project():  # 測試太多東西
    response = await auth_client.post(...)
    assert response.status_code == 201
    assert response.json()["repo_url"] == expected_url
    assert response.json()["status"] == "CREATED"
    # ... 更多 assertions
```

## CI/CD 整合

### GitHub Actions 範例

建立 `.github/workflows/tests.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      mongodb:
        image: mongo:7
        ports:
          - 27017:27017

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        cd backend
        pip install -r requirements.txt

    - name: Run tests with coverage
      run: |
        cd backend
        pytest tests/ --cov=app --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./backend/coverage.xml
        fail_ci_if_error: true
```

## 總結

### 基本指令速查

```bash
# 執行所有測試
pytest tests/ -v

# 執行單元測試
pytest tests/unit/ -v

# 生成覆蓋率報告
pytest tests/ --cov=app --cov-report=html

# 並行執行
pytest tests/ -n auto

# 只執行失敗的測試
pytest tests/ --lf
```

### 需要幫助？

1. 查看測試文件: `tests/TEST_SUMMARY.md`
2. 查看特定測試檔案的 docstring
3. 使用 `pytest --fixtures` 查看可用的 fixtures
4. 使用 `pytest --help` 查看所有選項

祝測試順利！🚀

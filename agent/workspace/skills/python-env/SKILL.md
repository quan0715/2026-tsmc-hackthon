---
name: python-env-setup
description: 使用此技能來設置 Python 開發環境、安裝依賴套件、配置虛擬環境。當用戶請求設置 Python 環境、安裝 pip 套件、或執行 Python 程式碼遇到模組缺失時使用。
---

# Python 環境設置技能

## 概述

此技能指導你如何在工作區中設置和管理 Python 開發環境。

## 環境檢查

### 1. 檢查 Python 版本

首先使用 `bash` 工具檢查已安裝的 Python 版本：

```
bash(command="python3 --version")
```

預期輸出類似：`Python 3.11.x`

### 2. 檢查 pip 版本

```
bash(command="pip3 --version")
```

## 安裝依賴套件

### 從 requirements.txt 安裝

如果專案有 `requirements.txt` 檔案：

```
bash(command="pip3 install -r requirements.txt")
```

### 安裝單一套件

```
bash(command="pip3 install <package_name>")
```

常用套件範例：
- `pytest` - 測試框架
- `black` - 程式碼格式化
- `flake8` - 程式碼檢查
- `mypy` - 類型檢查
- `requests` - HTTP 請求

### 安裝特定版本

```
bash(command="pip3 install package_name==1.2.3")
```

## 虛擬環境（可選）

如果需要隔離的環境：

### 創建虛擬環境

```
bash(command="python3 -m venv .venv")
```

### 啟用虛擬環境

在執行命令時指定虛擬環境的 Python：

```
bash(command=".venv/bin/pip install -r requirements.txt")
```

## 執行 Python 程式碼

### 執行現有檔案

```
bash(command="python3 main.py")
```

### 執行程式碼片段

先用 `write_file` 寫入檔案，再執行：

```
write_file("/workspace/repo/check_env.py", """
import sys
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")
""")
bash(command="python3 /workspace/repo/check_env.py")
```

### 執行測試

```
bash(command="python3 -m pytest tests/ -v")
```

## 常見問題排解

### ModuleNotFoundError

當遇到模組找不到的錯誤時：

1. 確認套件名稱（pip 套件名可能與 import 名稱不同）
2. 使用 `pip3 install <package>` 安裝缺失的套件
3. 檢查 requirements.txt 是否包含該套件

### 權限問題

如果遇到權限問題，使用 `--user` 標誌：

```
bash(command="pip3 install --user <package_name>")
```

## 最佳實踐

1. **總是先檢查 requirements.txt** - 大多數專案會列出所需依賴
2. **使用 pip freeze 記錄依賴** - `pip3 freeze > requirements.txt`
3. **執行前先安裝依賴** - 避免 ImportError
4. **使用 -v 參數獲取詳細輸出** - 便於排錯

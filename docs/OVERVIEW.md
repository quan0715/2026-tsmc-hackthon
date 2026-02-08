# Overview

Reforge (auto-refactor-agent) 是一套「以隔離容器執行」的程式碼分析與重構服務。

核心概念：

- 使用者在前端建立 Project，並提供 repo 與重構規格 (`spec`)
- Backend 會為每個 Project 建立獨立的 Docker container (Project Container)
- Project Container 內執行 AI Server + Agent，並在隔離環境中 clone repo、跑工具、產出 artifacts

## 系統組成

- Frontend: React/Vite，提供 UI
- Backend API: FastAPI，負責專案管理、認證、容器生命週期、轉發日誌串流
- MongoDB: 專案/使用者等資料
- PostgreSQL: Agent/LangGraph 會話持久化
- Project Container: 以 `refactor-base:latest` 為基底，執行 AI Server (`agent/ai_server.py`)

## 高層資料流

1. 使用者透過 UI/API 建立專案 (Project)
2. Provision 時 Backend 會建立 Project Container 並準備 workspace
3. Run Agent 時 Backend 呼叫 Project Container 內的 AI Server `/run`
4. Backend 轉發 Project Container 的日誌串流到 `.../stream` 端點供前端顯示

## 關鍵文件

- 啟動與開發: `docs/GETTING_STARTED.md`
- 使用流程: `docs/USAGE.md`
- 部署: `docs/DEPLOYMENT.md`
- 詳細 API: `docs/API.md` 或 `http://localhost:8000/docs`

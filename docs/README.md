# 文件索引

本目錄是 Reforge (auto-refactor-agent) 的主要文件入口。若你要快速啟動與部署，先看本頁的「入門」與「部署」。

## 入門 (推薦先讀)

- `docs/OVERVIEW.md`: 系統概念與高層架構
- `docs/GETTING_STARTED.md`: 本機啟動 (Docker Compose / 本地開發) 的最短路徑
- `docs/CONFIGURATION.md`: `backend/.env` 變數說明與必要設定
- `docs/USAGE.md`: UI/API 的基本使用流程 (建立專案 -> provision -> run agent -> 串流日誌)

## 執行與維運

- `docs/RUN_AND_DEV.md`: 常用腳本、開發模式、base image 相關操作
- `docs/DEPLOYMENT.md`: GCE/Prod 啟用與部署重點
- `docs/VERTEX_AI.md`: Vertex AI 設定（選用）
- `docs/TROUBLESHOOTING.md`: 常見問題與排除

## 參考文件 (需要細節時再查)

- `docs/API.md`: REST API 規格 (也可直接用 `http://localhost:8000/docs`)
- `docs/BACKEND.md`: 後端架構/模組/資料模型
- `docs/guides/`: CLI 使用指南
- `docs/testing/`: 測試相關文件

## CI/CD 與部署工作流程

GitHub Actions 說明與 GCE 部署細節：

- `.github/workflows/README.md`
- `.github/workflows/GCE_DEPLOY.md`

## 歷史與封存

過去的變更記錄、一次性報告、開發筆記放在 `docs/archives/`。這些內容保留作為參考，不建議作為最新行為的依據。

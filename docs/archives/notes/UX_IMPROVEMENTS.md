# Agent Run 自動重連 UX 改進

## 改進概述

實作了前端自動偵測並重連執行中的 Agent Run，提升了使用者體驗，解決了網頁重開後無法繼續查看執行日誌的問題。

## 新增功能

### 1. 自動重連機制 (`useAgentRunStream` Hook)

**位置**: `frontend/src/hooks/useAgentRunStream.ts`

**功能**:
- 自動偵測 `RUNNING` 狀態的 Agent Run
- 自動啟動 SSE 日誌串流
- 支援重連提示和狀態追蹤
- 清理連線避免記憶體洩漏

**使用方式**:
```typescript
const { isStreaming, isReconnecting } = useAgentRunStream({
  projectId,
  runId: currentRun?.id || null,
  isRunning: currentRun?.status === 'RUNNING',
  onLogEvent: (event) => {
    // 處理日誌事件
  },
  onReconnect: () => {
    // 顯示重連提示
  },
})
```

### 2. Toast 通知系統

**位置**:
- `frontend/src/components/ui/toast.tsx` - Toast 組件
- `frontend/src/hooks/useToast.ts` - Toast 管理 Hook

**功能**:
- 支援 4 種類型: `success`, `error`, `info`, `loading`
- 自動消失（可配置時間）
- 優雅的動畫效果
- 支援手動關閉

**使用方式**:
```typescript
const toast = useToast()

toast.info('偵測到執行中的任務，正在重新連線...')
toast.success('操作成功！')
toast.error('操作失敗')
toast.loading('處理中...') // 不會自動消失
```

### 3. Agent Run 面板 (`AgentRunPanel`)

**位置**: `frontend/src/components/agent/AgentRunPanel.tsx`

**功能**:
- 顯示 Agent Run 狀態（執行中/完成/失敗/停止）
- 即時串流日誌並分類顯示
- 顯示重連狀態
- 支援任務列表顯示
- 自動滾動到最新日誌

**日誌類型支援**:
- `ai_content` - AI 回應內容（Markdown 渲染）
- `tool_call` / `tool_calls` - 工具呼叫
- `tool_result` - 工具執行結果
- `thinking` - AI 思考過程
- `token_usage` - Token 使用統計
- `status` - 狀態更新
- `log` - 一般日誌

## UI/UX 改進

### 重連流程

1. **頁面載入時**
   - `useAgentRuns` 自動 polling 檢查任務狀態
   - 偵測到 `RUNNING` 狀態的任務

2. **自動重連**
   - `useAgentRunStream` 自動啟動 SSE 連線
   - 顯示 Toast 通知: "偵測到執行中的任務，正在重新連線..."
   - Panel 顯示 "重新連線中..." 狀態

3. **重連完成**
   - 接收到第一個日誌事件後，清除重連狀態
   - 開始即時串流日誌
   - Footer 顯示 "即時串流中" 指示器

### 視覺反饋

- **執行中狀態**: 紫色旋轉圖示 + "執行中" 標籤
- **重連中**: "重新連線中..." 脈衝動畫
- **串流中**: 綠色點 + "即時串流中" 指示器
- **Toast 通知**: 右上角浮動通知，3 秒後自動消失

## 檔案結構

```
frontend/src/
├── hooks/
│   ├── useAgentRunStream.ts    # 自動重連 Hook
│   └── useToast.ts              # Toast 管理 Hook
├── components/
│   ├── agent/
│   │   └── AgentRunPanel.tsx   # Agent Run 面板
│   └── ui/
│       └── toast.tsx            # Toast 通知組件
└── pages/
    └── ProjectDetailPage.tsx    # 整合所有改進
```

## 技術細節

### 自動清理機制

```typescript
useEffect(() => {
  if (isRunning && runId) {
    startStream()
  } else {
    cleanup() // 自動清理連線
  }
  return cleanup // 組件卸載時清理
}, [isRunning, runId, startStream, cleanup])
```

### 避免重複連線

```typescript
const startStream = useCallback(async () => {
  if (!projectId || !runId || !isRunning) return
  if (isStreaming) return // 避免重複連線

  // ... 啟動串流
}, [projectId, runId, isRunning, isStreaming, ...])
```

### 狀態持久化

透過 `hasReconnectedRef` 追蹤是否為重連（而非首次載入），避免在首次載入時顯示重連提示。

## 測試建議

### 測試重連功能

1. 啟動一個 Agent Run
2. 關閉瀏覽器分頁
3. 重新打開專案詳情頁
4. 確認:
   - Toast 顯示重連提示
   - Agent Run Panel 顯示 "重新連線中..."
   - 開始接收日誌後，重連狀態消失
   - Footer 顯示 "即時串流中"

### 測試 Toast 通知

```typescript
// 在瀏覽器 console 測試
toast.info('測試訊息')
toast.success('成功訊息', 5000) // 5 秒後消失
toast.error('錯誤訊息')
const loadingId = toast.loading('載入中...')
setTimeout(() => toast.removeToast(loadingId), 3000) // 3 秒後移除
```

## 已知限制

1. **容器重啟**: 如果 Docker 容器重啟，記憶體中的任務狀態會消失（但 PostgreSQL 會話歷史保留）
2. **日誌緩衝**: 目前不會回補網頁關閉期間錯過的日誌（可考慮未來改進）
3. **並發限制**: 一個專案同時只能有一個 RUNNING 的任務

## 未來改進方向

1. **歷史日誌回補**: 重連時載入錯過的日誌
2. **離線指示**: 顯示網路斷線狀態
3. **自動重試**: SSE 連線失敗時自動重試（帶指數退避）
4. **持久化通知**: 將重要通知儲存到 localStorage
5. **任務列表視圖**: 顯示所有歷史任務的列表頁面

## 相關 PR / Issues

- 功能需求: 前端重開時自動判斷是否需要繼續 streaming
- 改進目標: 提升 UX，避免使用者遺失執行狀態

# 測試 Agent Run 自動重連 UX 改進

## 前置準備

### 1. 啟動服務

```bash
# 啟動 PostgreSQL (Docker)
docker run -d --name postgres-test \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=langgraph \
  -p 5432:5432 \
  postgres:16

# 啟動 Backend API
cd backend
source venv/bin/activate
POSTGRES_URL="postgresql://postgres:postgres@localhost:5432/langgraph" \
uvicorn app.main:app --reload

# 啟動 Frontend
cd frontend
npm run dev
```

### 2. 創建測試專案

1. 註冊/登入帳號
2. 建立一個新專案
3. Provision 專案（建立容器）

## 測試案例

### 測試 1: 基本自動重連功能

**目的**: 驗證網頁重開後能自動偵測並重連執行中的任務

**步驟**:
1. 在專案詳情頁點擊「開始重構」
2. 觀察 Agent Run Panel 顯示「執行中」狀態
3. 等待幾秒，確認日誌開始串流
4. **關閉瀏覽器分頁**
5. 重新打開專案詳情頁

**預期結果**:
- ✅ 右上角顯示 Toast 通知: "偵測到執行中的任務，正在重新連線..."
- ✅ Agent Run Panel 顯示 "重新連線中..." 狀態（脈衝動畫）
- ✅ 2-3 秒後開始接收日誌
- ✅ 重連狀態消失，顯示 "即時串流中" 指示器
- ✅ 日誌持續更新

**截圖位置**: 重連時的 Toast 和 Panel 狀態

---

### 測試 2: Toast 通知系統

**目的**: 驗證 Toast 通知的各種類型和行為

**步驟**:
1. 開啟瀏覽器 Console（F12）
2. 執行以下測試指令:

```javascript
// 測試 info 通知
toast.info('這是一條測試訊息')

// 測試 success 通知（5 秒後消失）
toast.success('操作成功！', 5000)

// 測試 error 通知
toast.error('操作失敗：連線逾時')

// 測試 loading 通知（不會自動消失）
const loadingId = toast.loading('正在處理中...')

// 3 秒後手動移除 loading
setTimeout(() => toast.removeToast(loadingId), 3000)

// 測試多個通知同時顯示
toast.info('通知 1')
setTimeout(() => toast.success('通知 2'), 500)
setTimeout(() => toast.error('通知 3'), 1000)
```

**預期結果**:
- ✅ 每個 Toast 顯示正確的圖示和顏色
  - Info: 藍色 + 資訊圖示
  - Success: 綠色 + 勾選圖示
  - Error: 紅色 + 警告圖示
  - Loading: 紫色 + 旋轉圖示
- ✅ Info/Success/Error 在指定時間後自動消失
- ✅ Loading 不會自動消失，需手動關閉
- ✅ 多個 Toast 垂直堆疊顯示
- ✅ 淡入淡出動畫流暢

---

### 測試 3: Agent Run Panel 日誌顯示

**目的**: 驗證不同類型日誌的顯示格式

**步驟**:
1. 啟動一個 Agent Run
2. 觀察 Agent Run Panel 的日誌輸出
3. 檢查以下日誌類型的顯示:
   - AI 回應內容 (ai_content)
   - 工具呼叫 (tool_call)
   - 工具結果 (tool_result)
   - 思考過程 (thinking)
   - Token 使用統計 (token_usage)
   - 狀態更新 (status)

**預期結果**:
- ✅ `ai_content`: 使用 Markdown 渲染，支援格式化
- ✅ `tool_call`: 顯示藍色工具圖示 🔧，展開顯示參數
- ✅ `tool_result`: 顯示綠色勾選 ✓，展開顯示輸出
- ✅ `thinking`: 黃色斜體 💭
- ✅ `token_usage`: 灰色統計 📊
- ✅ 自動滾動到最新日誌
- ✅ 時間戳格式正確

---

### 測試 4: 任務列表整合

**目的**: 驗證 Agent Run Panel 與任務列表的整合

**步驟**:
1. 啟動 Agent Run
2. 等待 AI 生成任務列表 (task_list 事件)
3. 觀察任務顯示

**預期結果**:
- ✅ Panel 上方顯示任務列表
- ✅ 任務狀態即時更新（pending → in_progress → completed）
- ✅ 任務列表摺疊/展開功能正常
- ✅ 左側 Info Panel 也同步顯示任務

---

### 測試 5: 多個專案並發

**目的**: 驗證多個專案的 Agent Run 互不干擾

**步驟**:
1. 建立兩個測試專案 (Project A, Project B)
2. 在 Project A 啟動 Agent Run
3. 切換到 Project B 啟動 Agent Run
4. 在兩個專案間切換

**預期結果**:
- ✅ 每個專案的日誌串流獨立
- ✅ 切換專案時自動清理舊連線
- ✅ 切換回來時自動重連
- ✅ 不會出現日誌混亂

---

### 測試 6: 錯誤處理

**目的**: 驗證異常情況的處理

**測試案例**:

#### 6.1 容器未啟動
1. 停止專案容器: `docker stop refactor-project-{id}`
2. 嘗試啟動 Agent Run

**預期**: 顯示錯誤 Toast 並說明容器未啟動

#### 6.2 網路斷線
1. 啟動 Agent Run
2. 關閉網路連線
3. 等待 SSE 連線中斷

**預期**: 顯示錯誤狀態，提示重新連線

#### 6.3 任務失敗
1. 啟動 Agent Run
2. 等待任務執行失敗

**預期**:
- ✅ Agent Run Panel 顯示「失敗」狀態（紅色）
- ✅ 顯示錯誤訊息
- ✅ 停止日誌串流

---

### 測試 7: 停止和恢復

**目的**: 驗證停止和恢復功能

**步驟**:
1. 啟動 Agent Run
2. 點擊「Stop」按鈕
3. 確認任務停止
4. 點擊「Resume」按鈕（如果有）

**預期結果**:
- ✅ Stop: 任務狀態變為 STOPPED，日誌停止
- ✅ Resume: 使用相同 thread_id 繼續對話
- ✅ 歷史對話保留（PostgreSQL 持久化）

---

## 效能測試

### 測試 8: 長時間執行

**目的**: 驗證長時間執行的穩定性

**步驟**:
1. 啟動一個預計執行 5-10 分鐘的 Agent Run
2. 保持頁面開啟
3. 觀察記憶體使用和 CPU 使用

**預期結果**:
- ✅ 記憶體使用穩定，不會持續增長
- ✅ CPU 使用合理
- ✅ 日誌顯示流暢，無卡頓
- ✅ SSE 連線穩定，不會斷線

---

### 測試 9: 快速切換

**目的**: 驗證快速切換專案的穩定性

**步驟**:
1. 在多個專案間快速切換（5 秒切換一次）
2. 每個專案都有執行中的任務
3. 重複 10 次

**預期結果**:
- ✅ 無記憶體洩漏
- ✅ 舊連線正確清理
- ✅ 新連線正確建立
- ✅ 無 JavaScript 錯誤

---

## 瀏覽器相容性

### 測試 10: 跨瀏覽器測試

**測試環境**:
- Chrome (最新版本)
- Firefox (最新版本)
- Safari (macOS)
- Edge (Windows)

**預期**: 所有功能在各瀏覽器中正常運作

---

## 常見問題排查

### Q1: Toast 不顯示
**檢查**:
- `<ToastContainer>` 是否正確放置在頁面中
- `useToast` hook 是否正確使用
- Console 是否有錯誤訊息

### Q2: 重連失敗
**檢查**:
- 容器是否正在運行: `docker ps`
- Backend API 是否正常: `curl http://localhost:8000/api/v1/health`
- 瀏覽器 Network 分頁查看 SSE 連線狀態

### Q3: 日誌不更新
**檢查**:
- Agent Run 狀態是否為 RUNNING
- SSE stream 是否建立成功
- Console 是否有 JavaScript 錯誤

### Q4: 記憶體洩漏
**檢查**:
- 使用 Chrome DevTools Memory 分析
- 確認 `cleanup` 函數正確執行
- 檢查 `useEffect` 的 return cleanup

---

## 測試報告模板

```markdown
# UX 改進測試報告

**測試日期**: YYYY-MM-DD
**測試人員**: [姓名]
**瀏覽器**: Chrome 120.x

## 測試結果

### 基本功能
- [ ] 自動重連: ✅ Pass / ❌ Fail
- [ ] Toast 通知: ✅ Pass / ❌ Fail
- [ ] 日誌顯示: ✅ Pass / ❌ Fail
- [ ] 任務列表: ✅ Pass / ❌ Fail

### 錯誤處理
- [ ] 容器未啟動: ✅ Pass / ❌ Fail
- [ ] 網路斷線: ✅ Pass / ❌ Fail
- [ ] 任務失敗: ✅ Pass / ❌ Fail

### 效能測試
- [ ] 長時間執行: ✅ Pass / ❌ Fail
- [ ] 快速切換: ✅ Pass / ❌ Fail

## 發現的問題

1. [問題描述]
   - 重現步驟: ...
   - 預期結果: ...
   - 實際結果: ...
   - 嚴重程度: Critical / High / Medium / Low

## 改進建議

1. [建議 1]
2. [建議 2]

## 截圖

[附上相關截圖]
```

---

## 自動化測試 (未來)

建議使用 Playwright 或 Cypress 實作以下自動化測試:

1. **E2E 重連測試**: 模擬頁面重新載入
2. **Toast 測試**: 驗證通知顯示和消失
3. **SSE 連線測試**: 模擬網路中斷和恢復
4. **記憶體洩漏測試**: 使用 Puppeteer Memory API

範例程式碼（Playwright）:

```typescript
test('agent run auto-reconnect', async ({ page, context }) => {
  // 1. 啟動 Agent Run
  await page.goto('/projects/123')
  await page.click('[data-testid="start-refactor"]')
  await page.waitForSelector('[data-testid="agent-running"]')

  // 2. 重新載入頁面
  await page.reload()

  // 3. 驗證重連
  await expect(page.locator('[data-testid="toast-info"]')).toBeVisible()
  await expect(page.locator('[data-testid="reconnecting"]')).toBeVisible()

  // 4. 驗證串流恢復
  await page.waitForSelector('[data-testid="streaming-indicator"]', { timeout: 5000 })
})
```

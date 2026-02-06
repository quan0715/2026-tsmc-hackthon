此檔案由 Agent 在執行過程中維護，用於跨迭代保留關鍵上下文。
角色定義、工作流程、工具說明等由系統提示負責，此處不重複。

## 專案上下文
- 原始語言:
- 目標語言:
- 測試命令:
- 運行命令:
- 特殊注意事項:


## 工作目錄（嚴格遵守）

```
/workspace/
├── repo/           # 原始碼（只讀）
├── refactor-repo/  # 重構碼（你的工作區）
├── memory/         # 記憶系統文件
│   ├── AGENTS.md      # 你的角色定義（只讀參考）
│   ├── CHECKLIST.md   # 快速進度清單（每輪必更新）
│   ├── plan.md        # 詳細重構計劃（每輪必更新）
│   └── learnings.md   # 錯誤模式知識庫（可選）
└── artifacts/      # 最終產出

```

## 記憶系統文件

### 1. CHECKLIST.md（快速儀表板）

位置：`/workspace/memory/CHECKLIST.md`


格式：
```markdown
# 重構 Checklist

## 目標
[一句話描述重構目標]

## 環境
- 原始語言: xxx
- 目標語言: xxx
- 測試命令: `xxx`
- 運行命令: `xxx`

## 進度
- [x] 環境設置完成
- [x] 已完成項目
- [ ] 待完成項目

## 本輪迭代
完成: xxx
問題: xxx（如有）
下一步: xxx
```

**不需要：**
- 時間估計
- 詳細計劃表
- 架構設計文檔
- 多個分析報告
- 超過上述 3 個文件以外的文

## 工具

### bash
```
bash(command="go test ./...")
bash(command="cd /workspace/refactor-repo && go run main.go")
```

### env-setup subagent
```
task(name="env-setup", task="設置 Go 環境")
```

## 工作流程

1. 讀取 `/workspace/repo/` 了解專案
2. 設置環境（用 env-setup）
3. 寫代碼到 `/workspace/refactor-repo/`
4. 跑測試，修 bug
5. 更新 CHECKLIST.md
6. 重複直到完成

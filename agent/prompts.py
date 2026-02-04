"""提示詞管理 - 集中管理所有 AI 提示詞"""

from typing import Optional


# === 系統提示詞 ===
SYSTEM_PROMPT = """你是 CQ，一個專業的程式碼重構 AI Agent。

## 核心原則

1. **目標導向**：專注完成重構任務，不寫冗餘文檔
2. **精簡記錄**：文檔是給 AI 自己看的，只記關鍵資訊
3. **持續迭代**：每輪更新 checklist，直到目標完成

## 工作目錄（嚴格遵守）

```
/workspace/
├── repo/           # 原始碼（只讀）
├── refactor-repo/  # 重構碼（你的工作區）
├── memory/         # 只放 CHECKLIST.md
└── artifacts/      # 最終產出
```

**禁止創建其他目錄或文件！**

## 唯一文檔：CHECKLIST.md

位置：`/workspace/memory/CHECKLIST.md`

內容：目標、環境、進度 checklist、本輪迭代摘要

**不需要**：時間估計、詳細計劃表、架構設計文檔、多個報告

## 工作流程

1. 讀取 `/workspace/repo/` 了解專案
2. 設置環境（用 env-setup subagent）
3. 寫代碼到 `/workspace/refactor-repo/`
4. 跑測試，修 bug
5. 更新 CHECKLIST.md
6. 重複直到完成
"""

# === 使用者訊息模板 ===
USER_MESSAGE_TEMPLATE = """請分析程式碼庫並將分析結果寫入檔案。

# 程式碼庫路徑
{repo_path}

# 分析需求
{init_prompt}

# 任務要求
1. 使用 ls 和 read_file 工具深入探索和分析 {repo_path} 目錄中的程式碼
2. 根據用戶需求進行針對性分析
3. 將分析結果寫入 Markdown 檔案
4. **重要**: 使用 write_file 工具,將結果寫入完整路徑 {artifacts_path}/plan.md

注意:
- 必須使用完整的絕對路徑 {artifacts_path}/plan.md
- 如果 {artifacts_path} 目錄不存在,請先創建它

分析內容應包括(但不限於):
- 程式碼庫結構概覽
- 主要組件和模組
- 架構設計和模式
- 發現的問題和改進建議
- 具體的行動建議

請開始分析並生成檔案。
"""


# === Prompt 變體 (可擴展) ===
PROMPT_VARIANTS = {
    "default": SYSTEM_PROMPT,
    "verbose": SYSTEM_PROMPT + "\n請提供詳細的分析和大量範例。",
    "concise": SYSTEM_PROMPT + "\n請提供簡潔精煉的分析,聚焦於最關鍵的問題。",
}


def get_system_prompt(
    variant: str = "default",
    include_tool_descriptions: bool = True,
) -> str:
    """取得系統提示詞

    Args:
        variant: 提示詞變體 (default, verbose, concise)
        include_tool_descriptions: 是否包含工具描述（從 registry 取得）

    Returns:
        系統提示詞字串
    """
    base_prompt = PROMPT_VARIANTS.get(variant, SYSTEM_PROMPT)

    if include_tool_descriptions:
        # 延遲 import 避免循環依賴
        from agent.registry import get_tool_descriptions
        tool_descriptions = get_tool_descriptions()
        if tool_descriptions:
            base_prompt = f"{base_prompt}\n\n{tool_descriptions}"

    return base_prompt


def get_tool_descriptions_section() -> str:
    """單獨取得工具描述區塊

    Returns:
        格式化的工具描述文字
    """
    from agent.registry import get_tool_descriptions
    return get_tool_descriptions()


def build_user_message(
    repo_path: str,
    artifacts_path: str,
    init_prompt: str
) -> str:
    """構建使用者訊息

    Args:
        repo_path: 程式碼庫路徑
        artifacts_path: 產出物路徑
        init_prompt: 初始提示

    Returns:
        格式化的使用者訊息
    """
    return USER_MESSAGE_TEMPLATE.format(
        repo_path=repo_path,
        artifacts_path=artifacts_path,
        init_prompt=init_prompt
    )


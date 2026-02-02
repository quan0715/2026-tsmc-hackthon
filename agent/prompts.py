"""提示詞管理 - 集中管理所有 AI 提示詞"""

# === 系統提示詞 ===
SYSTEM_PROMPT = """你是一個專業的程式碼分析專家 AI Agent。
你的任務是深入分析程式碼庫,並將分析結果寫入檔案。

工作流程:
1. 使用 ls 和 read_file 工具探索和分析程式碼庫
2. 理解程式碼結構、架構模式、主要組件
3. 識別程式碼品質問題、技術債、可改進的地方
4. 將你的分析結果寫入 Markdown 檔案

注意事項:
- 深入分析,提供有價值的見解
- 分析結果要清晰、具體、可操作
- 使用 Markdown 格式組織內容(標題、列表、程式碼區塊等)
- 不要只列出檔案清單,要提供實質性的分析和建議
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


def get_system_prompt(variant: str = "default") -> str:
    """取得系統提示詞

    Args:
        variant: 提示詞變體 (default, verbose, concise)

    Returns:
        系統提示詞字串
    """
    return PROMPT_VARIANTS.get(variant, SYSTEM_PROMPT)


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


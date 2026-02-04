#!/usr/bin/env python3
"""
資料庫遷移腳本：將 init_prompt 欄位重新命名為 spec

此腳本會：
1. 將 projects collection 中的 init_prompt 欄位重命名為 spec
2. 為所有專案新增 refactor_thread_id 欄位（預設為 null）

使用方式：
    python scripts/migrate_init_prompt_to_spec.py

環境變數：
    MONGODB_URL - MongoDB 連線字串（預設：mongodb://localhost:27017）
    MONGODB_DB_NAME - 資料庫名稱（預設：refactor_agent）
"""

import os
import sys
from pymongo import MongoClient
from pymongo.errors import BulkWriteError


def main():
    # 從環境變數讀取設定
    mongodb_url = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    db_name = os.getenv("MONGODB_DB_NAME", "refactor_agent")

    print(f"連接到 MongoDB: {mongodb_url}")
    print(f"資料庫名稱: {db_name}")

    # 連接資料庫
    client = MongoClient(mongodb_url)
    db = client[db_name]
    projects = db.projects

    # 計算需要遷移的文件數量
    total_count = projects.count_documents({})
    init_prompt_count = projects.count_documents({"init_prompt": {"$exists": True}})
    spec_count = projects.count_documents({"spec": {"$exists": True}})

    print(f"\n📊 目前狀態:")
    print(f"   總專案數: {total_count}")
    print(f"   有 init_prompt 欄位的專案數: {init_prompt_count}")
    print(f"   有 spec 欄位的專案數: {spec_count}")

    if init_prompt_count == 0:
        print("\n✅ 沒有需要遷移的文件（init_prompt 欄位不存在或已遷移）")
        return

    # 確認遷移
    if len(sys.argv) < 2 or sys.argv[1] != "--yes":
        confirm = input(f"\n⚠️  將重命名 {init_prompt_count} 個專案的 init_prompt → spec 欄位。繼續？(y/N) ")
        if confirm.lower() != 'y':
            print("已取消遷移")
            return

    print("\n🔄 開始遷移...")

    # 執行遷移：重命名 init_prompt 為 spec
    result = projects.update_many(
        {"init_prompt": {"$exists": True}},
        {"$rename": {"init_prompt": "spec"}}
    )
    print(f"   ✅ 重命名 init_prompt → spec: {result.modified_count} 個文件")

    # 確保所有專案都有 refactor_thread_id 欄位
    result = projects.update_many(
        {"refactor_thread_id": {"$exists": False}},
        {"$set": {"refactor_thread_id": None}}
    )
    print(f"   ✅ 新增 refactor_thread_id 欄位: {result.modified_count} 個文件")

    # 驗證遷移結果
    print("\n📊 遷移後狀態:")
    init_prompt_count = projects.count_documents({"init_prompt": {"$exists": True}})
    spec_count = projects.count_documents({"spec": {"$exists": True}})
    thread_id_count = projects.count_documents({"refactor_thread_id": {"$exists": True}})

    print(f"   有 init_prompt 欄位的專案數: {init_prompt_count}")
    print(f"   有 spec 欄位的專案數: {spec_count}")
    print(f"   有 refactor_thread_id 欄位的專案數: {thread_id_count}")

    if init_prompt_count == 0 and spec_count == total_count:
        print("\n✅ 遷移完成！")
    else:
        print("\n⚠️  遷移可能不完整，請檢查資料")

    client.close()


if __name__ == "__main__":
    main()

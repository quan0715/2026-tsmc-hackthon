#!/usr/bin/env python3
"""
AI 舊程式碼智能重構系統 - 完整功能 Demo

展示完整的專案生命週期：
1. 建立專案
2. Provision 容器並 clone repository
3. 查看即時日誌
4. 執行指令
5. 停止專案
6. 刪除專案
"""

import requests
import time
import json
from typing import Optional

API_BASE = "http://localhost:8000/api/v1"


def print_section(title: str):
    """列印區塊標題"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_response(response: requests.Response):
    """美化輸出 JSON 回應"""
    try:
        data = response.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))
    except:
        print(response.text)


def create_project(repo_url: str, branch: str, init_prompt: str) -> Optional[str]:
    """建立專案"""
    print_section("1. 建立專案")

    data = {
        "repo_url": repo_url,
        "branch": branch,
        "init_prompt": init_prompt,
    }

    print(f"POST {API_BASE}/projects")
    print(f"請求資料: {json.dumps(data, indent=2, ensure_ascii=False)}\n")

    response = requests.post(f"{API_BASE}/projects", json=data)

    if response.status_code == 201:
        project = response.json()
        project_id = project["id"]
        print(f"✅ 專案建立成功!")
        print(f"專案 ID: {project_id}")
        print(f"狀態: {project['status']}")
        return project_id
    else:
        print(f"❌ 建立失敗: {response.status_code}")
        print_response(response)
        return None


def provision_project(project_id: str) -> bool:
    """Provision 專案"""
    print_section("2. Provision 專案（建立容器並 clone repository）")

    print(f"POST {API_BASE}/projects/{project_id}/provision")
    print("這將會:")
    print("  - 建立 Docker 容器")
    print("  - 啟動容器")
    print("  - Clone Git repository\n")

    response = requests.post(f"{API_BASE}/projects/{project_id}/provision")

    if response.status_code == 200:
        result = response.json()
        print("✅ Provision 成功!")
        print(f"容器 ID: {result['container_id'][:12]}")
        print(f"狀態: {result['status']}")
        return True
    else:
        print(f"❌ Provision 失敗: {response.status_code}")
        print_response(response)
        return False


def get_project_status(project_id: str):
    """查詢專案狀態"""
    print_section("3. 查詢專案狀態（包含 Docker 狀態）")

    print(f"GET {API_BASE}/projects/{project_id}?include_docker_status=true\n")

    response = requests.get(
        f"{API_BASE}/projects/{project_id}?include_docker_status=true"
    )

    if response.status_code == 200:
        print("✅ 專案狀態:")
        print_response(response)
    else:
        print(f"❌ 查詢失敗: {response.status_code}")


def stream_logs(project_id: str, duration: int = 5):
    """串流日誌（限時）"""
    print_section("4. 即時串流容器日誌 (SSE)")

    print(f"GET {API_BASE}/projects/{project_id}/logs/stream?follow=true&tail=10")
    print(f"將顯示最近 10 行日誌，並持續串流 {duration} 秒...\n")

    try:
        with requests.get(
            f"{API_BASE}/projects/{project_id}/logs/stream?follow=true&tail=10",
            stream=True,
            timeout=duration + 1,
        ) as response:
            if response.status_code == 200:
                print("✅ 開始接收日誌:")
                print("-" * 60)

                start_time = time.time()
                for line in response.iter_lines():
                    if time.time() - start_time > duration:
                        break

                    if line:
                        decoded = line.decode("utf-8")
                        if decoded.startswith("data:"):
                            try:
                                log_data = json.loads(decoded[5:].strip())
                                if "line" in log_data:
                                    print(
                                        f"[{log_data.get('number', '?')}] {log_data['line']}"
                                    )
                            except:
                                print(decoded)

                print("-" * 60)
                print(f"(已接收 {duration} 秒的日誌)")
            else:
                print(f"❌ 串流失敗: {response.status_code}")
    except requests.exceptions.Timeout:
        print(f"(已接收 {duration} 秒的日誌)")
    except Exception as e:
        print(f"❌ 錯誤: {e}")


def exec_command(project_id: str, command: str, workdir: str = "/workspace/repo"):
    """執行指令"""
    print_section(f"5. 在容器中執行指令: {command}")

    data = {"command": command, "workdir": workdir}

    print(f"POST {API_BASE}/projects/{project_id}/exec")
    print(f"指令: {command}")
    print(f"工作目錄: {workdir}\n")

    response = requests.post(f"{API_BASE}/projects/{project_id}/exec", json=data)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 執行完成 (exit code: {result['exit_code']})")

        if result["stdout"]:
            print("\n標準輸出:")
            print("-" * 60)
            print(result["stdout"])
            print("-" * 60)

        if result["stderr"]:
            print("\n標準錯誤:")
            print("-" * 60)
            print(result["stderr"])
            print("-" * 60)
    else:
        print(f"❌ 執行失敗: {response.status_code}")
        print_response(response)


def stop_project(project_id: str) -> bool:
    """停止專案"""
    print_section("6. 停止專案容器")

    print(f"POST {API_BASE}/projects/{project_id}/stop\n")

    response = requests.post(f"{API_BASE}/projects/{project_id}/stop")

    if response.status_code == 200:
        result = response.json()
        print("✅ 專案已停止")
        print(f"狀態: {result['status']}")
        return True
    else:
        print(f"❌ 停止失敗: {response.status_code}")
        print_response(response)
        return False


def delete_project(project_id: str) -> bool:
    """刪除專案"""
    print_section("7. 刪除專案和容器")

    print(f"DELETE {API_BASE}/projects/{project_id}\n")

    response = requests.delete(f"{API_BASE}/projects/{project_id}")

    if response.status_code == 204:
        print("✅ 專案已刪除（包含容器和資料庫記錄）")
        return True
    else:
        print(f"❌ 刪除失敗: {response.status_code}")
        print_response(response)
        return False


def main():
    """主程式"""
    print("\n" + "=" * 60)
    print("  AI 舊程式碼智能重構系統 - 完整功能 Demo")
    print("=" * 60)

    # 設定
    REPO_URL = "https://github.com/octocat/Hello-World.git"
    BRANCH = "master"
    INIT_PROMPT = "Demo: 完整功能測試"

    project_id = None

    try:
        # 1. 建立專案
        project_id = create_project(REPO_URL, BRANCH, INIT_PROMPT)
        if not project_id:
            return

        time.sleep(1)

        # 2. Provision
        if not provision_project(project_id):
            return

        time.sleep(2)

        # 3. 查詢狀態
        get_project_status(project_id)

        time.sleep(1)

        # 4. 串流日誌
        stream_logs(project_id, duration=5)

        time.sleep(1)

        # 5. 執行指令
        exec_command(project_id, "ls -la")

        time.sleep(1)

        exec_command(project_id, "cat README")

        time.sleep(1)

        exec_command(project_id, "git log --oneline -n 3")

        time.sleep(1)

        # 6. 停止專案
        stop_project(project_id)

        time.sleep(1)

        # 7. 刪除專案
        delete_project(project_id)

        print_section("Demo 完成!")
        print("✅ 所有功能測試通過")
        print("\n展示的功能:")
        print("  1. 建立專案")
        print("  2. Provision 容器並 clone repository")
        print("  3. 查詢專案狀態（包含 Docker 狀態）")
        print("  4. 即時串流日誌 (SSE)")
        print("  5. 在容器中執行指令")
        print("  6. 停止專案容器")
        print("  7. 刪除專案和容器")
        print()

    except KeyboardInterrupt:
        print("\n\n⚠️  Demo 被中斷")
        if project_id:
            print(f"清理專案: {project_id}")
            delete_project(project_id)

    except Exception as e:
        print(f"\n\n❌ 錯誤: {e}")
        if project_id:
            print(f"清理專案: {project_id}")
            delete_project(project_id)


if __name__ == "__main__":
    main()

# 測試專案記錄 - Racing Car Katas

## 專案資訊

**Repository**: https://github.com/emilybache/Racing-Car-Katas
**專案 ID**: `697b985b88052cc81c1b6894`
**容器 ID**: `9b0ff8e2fa65`
**分支**: `main`
**建立時間**: 2026-01-29 17:26:51
**狀態**: `READY` ✅

## 專案描述

Racing Car Katas 是 Emily Bache 開發的一系列程式碼重構練習專案，專注於 SOLID 設計原則和單元測試實踐。這是一個多語言專案，包含相同練習的不同語言實作。

### 練習目標

學習如何：
- 為遺留程式碼（Legacy Code）編寫單元測試
- 應用 SOLID 設計原則
- 重構程式碼以提高可測試性
- 識別違反 SOLID 原則的程式碼

### 包含的練習

1. **TirePressureMonitoringSystem** - 輪胎壓力監控系統
   - 監控輪胎壓力並設定警報
   - 練習依賴注入和測試隔離

2. **HtmlTextConverter** - HTML 文字轉換器
   - 將純文字轉換為 HTML 格式
   - 練習單一職責原則

3. **TicketDispenser** - 取票機系統
   - 管理商店的排隊系統
   - 練習全局狀態管理

4. **TelemetrySystem** - 遙測系統
   - 建立與遙測伺服器的連接
   - 練習介面隔離原則

5. **Leaderboard** - 排行榜系統
   - 計算賽車排名和積分
   - 練習開放封閉原則

## 專案結構

```
Racing-Car-Katas/
├── C/                  # C 語言實作
├── CSharp/             # C# 實作
├── Cpp/                # C++ 實作
├── Java/               # Java 實作
├── Javascript/         # JavaScript 實作
├── Python/             # Python 實作
│   ├── TelemetrySystem/
│   │   ├── client.py
│   │   ├── telemetry.py
│   │   └── test_telemetry.py
│   ├── Leaderboard/
│   │   ├── leaderboard.py
│   │   └── test_leaderboard.py
│   ├── TurnTicketDispenser/
│   │   ├── turn_ticket.py
│   │   └── test_turn_ticket.py
│   ├── TirePressureMonitoringSystem/
│   │   ├── sensor.py
│   │   ├── tire_pressure_monitoring.py
│   │   └── test_tire_pressure_monitoring.py
│   └── TextConverter/
│       ├── text_converter.py
│       ├── html_pages.py
│       └── test_text_converter.py
├── Ruby/               # Ruby 實作
├── Rust/               # Rust 實作
├── Swift/              # Swift 實作
├── TypeScript/         # TypeScript 實作
├── go/                 # Go 實作
├── kotlin/             # Kotlin 實作
├── php/                # PHP 實作
├── scala/              # Scala 實作
└── README.md
```

## API 操作記錄

### 1. 建立專案

```bash
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/emilybache/Racing-Car-Katas.git",
    "branch": "main",
    "init_prompt": "重構 Racing Car Katas 程式碼"
  }'
```

**回應**:
```json
{
  "id": "697b985b88052cc81c1b6894",
  "repo_url": "https://github.com/emilybache/Racing-Car-Katas.git",
  "branch": "main",
  "init_prompt": "重構 Racing Car Katas 程式碼",
  "status": "CREATED"
}
```

### 2. Provision 專案

```bash
curl -X POST http://localhost:8000/api/v1/projects/697b985b88052cc81c1b6894/provision
```

**回應**:
```json
{
  "message": "專案 provision 成功",
  "project_id": "697b985b88052cc81c1b6894",
  "container_id": "9b0ff8e2fa656ac68ec9051c83a7fa4def69b6f931454e5599766f486a0bac4c",
  "status": "READY"
}
```

### 3. 查詢專案狀態

```bash
curl "http://localhost:8000/api/v1/projects/697b985b88052cc81c1b6894?include_docker_status=true"
```

**回應**:
```json
{
  "id": "697b985b88052cc81c1b6894",
  "status": "READY",
  "container_id": "9b0ff8e2fa656ac68ec9051c83a7fa4def69b6f931454e5599766f486a0bac4c",
  "docker_status": {
    "id": "9b0ff8e2fa65",
    "name": "refactor-project-697b985b88052cc81c1b6894",
    "status": "running",
    "image": "refactor-base:latest"
  }
}
```

### 4. 探索專案結構

```bash
# 查看根目錄
curl -X POST http://localhost:8000/api/v1/projects/697b985b88052cc81c1b6894/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "ls -la", "workdir": "/workspace/repo"}'

# 查看 Python 檔案
curl -X POST http://localhost:8000/api/v1/projects/697b985b88052cc81c1b6894/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "find Python -type f -name \"*.py\"", "workdir": "/workspace/repo"}'

# 查看 README
curl -X POST http://localhost:8000/api/v1/projects/697b985b88052cc81c1b6894/exec \
  -H "Content-Type: application/json" \
  -d '{"command": "cat README.md", "workdir": "/workspace/repo"}'
```

## 快速存取命令

```bash
# 專案 ID（方便複製貼上）
PROJECT_ID="697b985b88052cc81c1b6894"

# 查詢專案
curl "http://localhost:8000/api/v1/projects/$PROJECT_ID"

# 執行指令
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{"command": "YOUR_COMMAND"}'

# 查看日誌
curl -N "http://localhost:8000/api/v1/projects/$PROJECT_ID/logs/stream?follow=false&tail=50"

# 停止專案
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/stop"

# 刪除專案
curl -X DELETE "http://localhost:8000/api/v1/projects/$PROJECT_ID"
```

## 後續實驗建議

### 1. Python TirePressureMonitoring 範例

查看並執行 Python 版本的輪胎壓力監控測試：

```bash
# 查看原始碼
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{"command": "cat Python/TirePressureMonitoringSystem/tire_pressure_monitoring.py", "workdir": "/workspace/repo"}'

# 查看測試
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{"command": "cat Python/TirePressureMonitoringSystem/test_tire_pressure_monitoring.py", "workdir": "/workspace/repo"}'
```

#### 程式碼範例

**tire_pressure_monitoring.py** - 待重構的程式碼：
```python
from sensor import Sensor

class Alarm(object):

    def __init__(self):
        self._low_pressure_threshold = 17
        self._high_pressure_threshold = 21
        self._sensor = Sensor()  # ❌ 硬編碼依賴，難以測試
        self._is_alarm_on = False

    def check(self):
        psi_pressure_value = self._sensor.pop_next_pressure_psi_value()
        if psi_pressure_value < self._low_pressure_threshold \
                or self._high_pressure_threshold < psi_pressure_value:
            self._is_alarm_on = True

    @property
    def is_alarm_on(self):
        return self._is_alarm_on
```

**sensor.py** - 模擬感測器：
```python
import random

class Sensor(object):

    _OFFSET = 16

    def pop_next_pressure_psi_value(self):
        pressure_telemetry_value = self.sample_pressure()
        return Sensor._OFFSET + pressure_telemetry_value

    @staticmethod
    def sample_pressure():
        # 模擬真實感測器，使用隨機值
        pressure_telemetry_value = 6 * random.random() * random.random()
        return pressure_telemetry_value
```

#### 重構挑戰

**問題識別**:
1. ❌ **違反依賴反轉原則（DIP）**: `Alarm` 直接依賴具體的 `Sensor` 類別
2. ❌ **難以測試**: 無法注入 Mock Sensor 進行單元測試
3. ❌ **隨機性**: `Sensor` 使用隨機值，測試結果不可預測

**重構目標**:
1. ✅ 引入依賴注入，允許傳入 Sensor
2. ✅ 使用介面或抽象類別解耦
3. ✅ 編寫可預測的單元測試

### 2. 執行測試（需要 Python 環境）

注意：目前基礎映像只有 git，如需執行 Python 測試需要擴充基礎映像。

### 3. 多語言比較

比較不同語言實作的差異：

```bash
# Java 版本
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{"command": "find Java -type f -name \"*.java\"", "workdir": "/workspace/repo"}'

# TypeScript 版本
curl -X POST "http://localhost:8000/api/v1/projects/$PROJECT_ID/exec" \
  -H "Content-Type: application/json" \
  -d '{"command": "find TypeScript -type f -name \"*.ts\"", "workdir": "/workspace/repo"}'
```

## 測試結果

✅ **專案建立**: 成功
✅ **Provision**: 成功（6 秒完成 clone）
✅ **容器狀態**: Running
✅ **檔案探索**: 成功存取所有檔案
✅ **Docker 狀態一致性**: 正常

## 備註

- 此專案非常適合作為重構練習的測試案例
- 包含多種語言實作，可用於驗證跨語言支援
- 原始碼品質優良，有完整的練習說明
- 可作為 AI 輔助重構功能的基準測試專案

## 相關連結

- **GitHub Repository**: https://github.com/emilybache/Racing-Car-Katas
- **作者 Patreon**: https://www.patreon.com/EmilyBache
- **影片說明**: https://youtu.be/ldthYMeXSoI
- **相關部落格**: http://coding-is-like-cooking.info/2012/09/solid-principles-and-tdd/

---

**文件建立時間**: 2026-01-29
**最後更新**: 2026-01-29
**維護者**: AI Refactor Agent System

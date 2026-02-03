---
name: go-env-setup
description: 使用此技能來設置 Go 開發環境、管理依賴、編譯和執行 Go 程式碼。當用戶請求設置 Go 環境、安裝 Go 模組、或執行 Go 程式碼遇到問題時使用。
---

# Go 環境設置技能

## 概述

此技能指導你如何在工作區中設置和管理 Go 開發環境。

## 環境檢查

### 1. 檢查 Go 版本

首先使用 `bash` 工具檢查已安裝的 Go 版本：

```
bash(command="go version")
```

預期輸出類似：`go version go1.21.0 linux/amd64`

### 2. 檢查 Go 環境變數

```
bash(command="go env GOPATH GOROOT GOCACHE")
```

## Go Modules 管理

### 初始化新模組

如果專案沒有 `go.mod` 檔案：

```
bash(command="go mod init <module_name>")
```

例如：
```
bash(command="go mod init github.com/user/project")
```

### 下載依賴

```
bash(command="go mod download")
```

### 整理依賴

自動添加缺失的依賴，移除未使用的依賴：

```
bash(command="go mod tidy")
```

### 安裝特定套件

```
bash(command="go get <package_path>")
```

常用套件範例：
- `github.com/gin-gonic/gin` - Web 框架
- `github.com/stretchr/testify` - 測試工具
- `github.com/spf13/cobra` - CLI 框架
- `gorm.io/gorm` - ORM 框架

## 執行 Go 程式碼

### 執行現有專案

執行 main package：

```
bash(command="go run .")
```

執行特定檔案：

```
bash(command="go run main.go")
```

執行子目錄的 main：

```
bash(command="go run ./cmd/server")
```

### 執行程式碼片段

先用 `write_file` 寫入檔案，再執行：

```
write_file("/workspace/repo/hello.go", """
package main

import "fmt"

func main() {
    fmt.Println("Hello, Go!")
}
""")
bash(command="go run /workspace/repo/hello.go")
```

## 編譯

### 編譯當前模組

```
bash(command="go build -o app .")
```

### 編譯特定平台

```
bash(command="GOOS=linux GOARCH=amd64 go build -o app-linux .")
```

## 測試

### 執行所有測試

```
bash(command="go test ./...")
```

### 執行測試並顯示詳細輸出

```
bash(command="go test -v ./...")
```

### 執行特定測試

```
bash(command="go test -v -run TestFunctionName ./...")
```

### 測試覆蓋率

```
bash(command="go test -cover ./...")
```

## 程式碼品質

### 格式化程式碼

```
bash(command="go fmt ./...")
```

### 靜態分析

```
bash(command="go vet ./...")
```

### 安裝並執行 golangci-lint

```
bash(command="go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest")
bash(command="golangci-lint run")
```

## 常見問題排解

### 找不到模組

當遇到 `cannot find module` 錯誤：

1. 確認專案有 `go.mod` 檔案
2. 執行 `go mod tidy` 下載依賴
3. 檢查模組路徑是否正確

### 編譯錯誤

使用詳細輸出來診斷：

```
bash(command="go build -v ./...")
```

### 權限問題（GOCACHE）

設置可寫的 cache 目錄：

```
bash(command="GOCACHE=/tmp/go-cache go build .")
```

## 最佳實踐

1. **總是先檢查 go.mod** - 了解專案的模組名稱和依賴
2. **使用 go mod tidy** - 保持依賴整潔
3. **執行前先下載依賴** - `go mod download`
4. **使用 go vet 檢查程式碼** - 發現潛在問題
5. **測試前格式化** - `go fmt ./...`

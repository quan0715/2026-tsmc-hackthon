---
name: go-env-setup
description: Use this skill to set up Go development environment, manage dependencies, compile and run Go code. Use when user requests Go environment setup, module installation, or encounters issues running Go code.
---

# Go Environment Setup Skill

## Overview

This skill guides you on how to set up and manage a Go development environment in the workspace.

## Environment Check

### 1. Check Go Version

First, use the `bash` tool to check the installed Go version:

```
bash(command="go version")
```

Expected output similar to: `go version go1.21.0 linux/amd64`

### 2. Check Go Environment Variables

```
bash(command="go env GOPATH GOROOT GOCACHE")
```

## Go Modules Management

### Initialize New Module

If the project doesn't have a `go.mod` file:

```
bash(command="go mod init <module_name>")
```

Example:
```
bash(command="go mod init github.com/user/project")
```

### Download Dependencies

```
bash(command="go mod download")
```

### Tidy Dependencies

Automatically add missing dependencies and remove unused ones:

```
bash(command="go mod tidy")
```

### Install Specific Package

```
bash(command="go get <package_path>")
```

Common package examples:
- `github.com/gin-gonic/gin` - Web framework
- `github.com/stretchr/testify` - Testing toolkit
- `github.com/spf13/cobra` - CLI framework
- `gorm.io/gorm` - ORM library

## Running Go Code

### Run Existing Project

Run main package:

```
bash(command="go run .")
```

Run specific file:

```
bash(command="go run main.go")
```

Run main in subdirectory:

```
bash(command="go run ./cmd/server")
```

### Run Code Snippet

First write to a file using `write_file`, then run it:

```
write_file("./repo/hello.go", """
package main

import "fmt"

func main() {
    fmt.Println("Hello, Go!")
}
""")
bash(command="go run ./repo/hello.go")
```

## Compilation

### Compile Current Module

```
bash(command="go build -o app .")
```

### Compile for Specific Platform

```
bash(command="GOOS=linux GOARCH=amd64 go build -o app-linux .")
```

## Testing

### Run All Tests

```
bash(command="go test ./...")
```

### Run Tests with Verbose Output

```
bash(command="go test -v ./...")
```

### Run Specific Test

```
bash(command="go test -v -run TestFunctionName ./...")
```

### Test Coverage

```
bash(command="go test -cover ./...")
```

## Code Quality

### Format Code

```
bash(command="go fmt ./...")
```

### Static Analysis

```
bash(command="go vet ./...")
```

### Install and Run golangci-lint

```
bash(command="go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest")
bash(command="golangci-lint run")
```

## Gin Web Framework

### Install Gin

```
bash(command="go get -u github.com/gin-gonic/gin")
```

### Basic Gin Application

Create a simple Gin web server:

```
write_file("./repo/main.go", """
package main

import (
    "github.com/gin-gonic/gin"
    "net/http"
)

func main() {
    r := gin.Default()
    
    r.GET("/ping", func(c *gin.Context) {
        c.JSON(http.StatusOK, gin.H{
            "message": "pong",
        })
    })
    
    r.Run(":8080")
}
""")
bash(command="go run main.go")
```

### Gin Routing Setup

#### RESTful API Routes

```go
r := gin.Default()

// GET request
r.GET("/users", getUsers)
r.GET("/users/:id", getUserByID)

// POST request
r.POST("/users", createUser)

// PUT request
r.PUT("/users/:id", updateUser)

// DELETE request
r.DELETE("/users/:id", deleteUser)
```

#### Route Groups

```go
v1 := r.Group("/api/v1")
{
    v1.GET("/users", getUsers)
    v1.POST("/users", createUser)
}

v2 := r.Group("/api/v2")
{
    v2.GET("/users", getUsersV2)
}
```

### Gin Middleware

#### Use Built-in Middleware

```go
r := gin.Default() // Includes Logger and Recovery middleware

// Or add manually
r := gin.New()
r.Use(gin.Logger())
r.Use(gin.Recovery())
```

#### Custom Middleware

```go
func AuthMiddleware() gin.HandlerFunc {
    return func(c *gin.Context) {
        token := c.GetHeader("Authorization")
        if token == "" {
            c.JSON(http.StatusUnauthorized, gin.H{"error": "unauthorized"})
            c.Abort()
            return
        }
        c.Next()
    }
}

// Use middleware
r.Use(AuthMiddleware())
```

### Gin Request Handling

#### Bind JSON Request

```go
type User struct {
    Name  string `json:"name" binding:"required"`
    Email string `json:"email" binding:"required,email"`
}

func createUser(c *gin.Context) {
    var user User
    if err := c.ShouldBindJSON(&user); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    c.JSON(http.StatusOK, user)
}
```

#### Query Parameters

```go
func getUsers(c *gin.Context) {
    page := c.DefaultQuery("page", "1")
    limit := c.Query("limit")
    c.JSON(http.StatusOK, gin.H{
        "page": page,
        "limit": limit,
    })
}
```

### Run Gin Application

#### Development Mode

```
bash(command="go run main.go")
```

#### Compile and Run

```
bash(command="go build -o server .")
bash(command="./server")
```

#### Specify Port

```go
r.Run(":3000") // Run on port 3000
```

### Gin Testing

Test Gin handler:

```go
func TestPingRoute(t *testing.T) {
    router := gin.Default()
    router.GET("/ping", func(c *gin.Context) {
        c.JSON(200, gin.H{"message": "pong"})
    })

    w := httptest.NewRecorder()
    req, _ := http.NewRequest("GET", "/ping", nil)
    router.ServeHTTP(w, req)

    assert.Equal(t, 200, w.Code)
    assert.Contains(t, w.Body.String(), "pong")
}
```

Run tests:

```
bash(command="go test -v ./...")
```

## Troubleshooting

### Module Not Found

When encountering `cannot find module` error:

1. Confirm project has `go.mod` file
2. Run `go mod tidy` to download dependencies
3. Check if module path is correct

### Compilation Errors

Use verbose output to diagnose:

```
bash(command="go build -v ./...")
```

### Permission Issues (GOCACHE)

Set writable cache directory:

```
bash(command="GOCACHE=/tmp/go-cache go build .")
```

## Best Practices

1. **Always check go.mod first** - Understand project module name and dependencies
2. **Use go mod tidy** - Keep dependencies clean
3. **Download dependencies before running** - `go mod download`
4. **Use go vet to check code** - Find potential issues
5. **Format before testing** - `go fmt ./...`

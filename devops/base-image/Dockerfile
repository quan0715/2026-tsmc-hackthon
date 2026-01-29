FROM alpine:3.19

# 安裝 git (最小依賴)
RUN apk add --no-cache git

# 建立工作目錄
RUN mkdir -p /workspace/repo

# 設定工作目錄
WORKDIR /workspace/repo

# 保持容器運行
CMD ["tail", "-f", "/dev/null"]

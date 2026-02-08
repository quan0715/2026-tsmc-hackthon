# Vertex AI (Optional)

本專案支援在「Project Container」中使用 Vertex AI 相關模型。重點在於：

1. Backend API 容器必須能存取 GCP credentials (ADC 或 Service Account JSON)
2. Backend 會把 credentials 轉掛載進每個 Project Container

## 本機 (Docker Compose 開發)

`devops/docker-compose.yml` 會把你本機的 ADC 檔案掛進 API 容器：

- host: `${HOME}/.config/gcloud/application_default_credentials.json`
- container: `/root/.config/gcloud/application_default_credentials.json`

你需要先在本機產生 ADC：

```bash
gcloud auth application-default login
```

然後在 `backend/.env` 設定：

```bash
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
```

若你想用顯式路徑，也可加上：

```bash
GOOGLE_APPLICATION_CREDENTIALS=/root/.config/gcloud/application_default_credentials.json
```

## 生產環境 (GCE/VM)

建議使用 Service Account JSON 或 VM 的預設服務帳號。

### 選項 A: 掛載 Service Account JSON (最直覺)

1. 把 SA JSON 放到主機上，例如 `/etc/reforge/sa.json`
2. 在 production compose 的 `api` service 增加 volume 掛載 (自行調整)：

```yaml
volumes:
  - /etc/reforge/sa.json:/run/secrets/gcp-sa.json:ro
```

3. 在 `backend/.env` 設定：

```bash
GCP_PROJECT_ID=your-gcp-project-id
GCP_LOCATION=us-central1
GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/gcp-sa.json
```

Backend 會將該檔案複製到 workspace volume，並掛載到 Project Container 內使用。

### 選項 B: 使用 ADC (若主機有 gcloud / 或透過其他方式提供 ADC)

確保 API 容器內有 `/root/.config/gcloud/application_default_credentials.json`，Backend 會自動偵測並轉掛載。

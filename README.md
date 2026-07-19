# Personal Link Hub

一個使用 Django 建立的單頁式個人連結首頁與短網址轉址服務。

## 技術架構

- Django 5.2
- `uv` 管理 Python 專案與 `uv.lock`
- PostgreSQL（本機使用 Docker Compose，正式環境可使用 Neon）
- Gunicorn 執行 WSGI
- WhiteNoise 在 Cloud Run 單容器中提供 production static files
- Docker／Docker Compose
- Cloud Run + Artifact Registry 或 Docker Hub（GCP 部署）
- Secret Manager 保存正式環境敏感設定
- Cloudflare 自訂網域、DNS、Proxy 與 HTTPS

## 功能

- `GET /`：公開個人連結首頁
- `GET /r/<slug>/`：HTTP 302 短網址轉址
- `GET /healthz/`：Cloud Run 健康檢查
- `/admin/`：Django Admin 管理個人資料與連結
- 只保存連結點擊總數與最後點擊時間，不保存原始 IP、User-Agent 或逐筆訪客資料

## 本機開發

需要 Python 3.12、uv 與 Docker Desktop。

```powershell
uv sync
Copy-Item .env.example .env
uv run python manage.py check
uv run python manage.py test
```

若要使用本機 PostgreSQL：

```powershell
docker compose --env-file .env.example up --build
```

網站會在 <http://localhost/> 開啟，Admin 位於 <http://localhost/admin/>。

若要直接使用 Neon，將 Neon 的 PostgreSQL pooled connection string 放入未追蹤的 `.env`：

```env
DATABASE_URL=postgresql://...-pooler.../neondb?sslmode=require
```

然後執行：

```powershell
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

## Docker 驗證

```powershell
docker build --tag personal-link-hub:local .
docker run --rm -p 8080:8080 `
  -e SECRET_KEY=local-only `
  -e ALLOWED_HOSTS=localhost,127.0.0.1 `
  personal-link-hub:local
```

正式容器會監聽 Cloud Run 注入的 `PORT`，若未設定則使用 8080。Cloud Run 會處理外部 HTTPS；本專案的 Nginx 只供本機 Compose 或自行管理的 VM 使用。

## Neon PostgreSQL

Neon 是外部託管的 PostgreSQL。Django 透過 `DATABASE_URL` 連線，模型和 migration 不需要依賴特定供應商。Cloud Run 上應使用 Neon pooled connection string，並將完整連線字串放入 GCP Secret Manager，不要放入 Git 或 Docker image。

## GCP 部署概念

```text
Dockerfile
    ↓ docker build
Artifact Registry 或 Docker Hub
    ↓
Cloud Run
    ↓ DATABASE_URL
Neon PostgreSQL
```

Cloud Run image 可以推送到 Artifact Registry，也可以推送到 Docker Hub。
Artifact Registry 適合正式環境；Docker Hub 適合目前的個人學習與低流量展示。
Cloudflare 自訂網域設定、Docker Hub 替代流程與測試方式請看
[`deploy/README.md`](deploy/README.md) 和 [`TESTING.md`](TESTING.md)。

建立 Artifact Registry repository 後，推送 image：

```powershell
$PROJECT_ID = "your-gcp-project"
$REGION = "asia-east1"
$REPOSITORY = "personal-link-hub"
$IMAGE = "$REGION-docker.pkg.dev/$PROJECT_ID/$REPOSITORY/web:latest"

gcloud auth configure-docker "$REGION-docker.pkg.dev"
docker build --tag $IMAGE .
docker push $IMAGE
```

將秘密加入 Secret Manager（值不要寫入 Git）：

```powershell
gcloud secrets create django-secret-key --replication-policy=automatic
gcloud secrets versions add django-secret-key --data-file="$env:TEMP\django-secret-key.txt"

gcloud secrets create database-url --replication-policy=automatic
gcloud secrets versions add database-url --data-file="$env:TEMP\database-url.txt"
```

部署 Cloud Run：

```powershell
gcloud run deploy personal-link-hub `
  --image $IMAGE `
  --region $REGION `
  --port 8080 `
  --allow-unauthenticated `
  --max 3 `
  --set-env-vars "^@^DEBUG=0@ALLOWED_HOSTS=SERVICE_URL_OR_DOMAIN@CSRF_TRUSTED_ORIGINS=https://SERVICE_URL_OR_DOMAIN" `
  --set-secrets "SECRET_KEY=django-secret-key:1,DATABASE_URL=database-url:1"
```

部署前後要確認：

```powershell
gcloud run services describe personal-link-hub --region $REGION
uv run python manage.py check --deploy
```

第一次部署時可以從本機透過同一個 Neon `DATABASE_URL` 執行 `migrate`；後續標準化部署應改成 Cloud Run Job 或 CI/CD release step 執行 migration，不要讓每個 Web container 同時執行 migration。

## 安全注意事項

- `.env`、Neon connection string、Django secret key 不得提交到 Git。
- 由於資料庫密碼曾被貼在對話中，正式上線前請在 Neon 重新產生密碼。
- `--allow-unauthenticated` 只讓公開首頁和短網址可被存取；Admin 仍由 Django 登入保護。
- GCP Billing 建立預算警示，並將 Cloud Run 最大 Instance 數設定為小於預期流量可承受的範圍。

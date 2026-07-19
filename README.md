# 個人網站導航頁

![Python Version](https://img.shields.io/badge/python-3.12-blue)
![Django Version](https://img.shields.io/badge/Django-5.2-0C4B33?logo=django&logoColor=white)
![uv](https://img.shields.io/badge/uv-managed-6A4C93?logo=uv&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)
![Docker Compose](https://img.shields.io/badge/Docker%20Compose-2496ED?logo=docker&logoColor=white)
![Gunicorn](https://img.shields.io/badge/Gunicorn-23.0-499848)
![Nginx](https://img.shields.io/badge/Nginx-1.27-009639?logo=nginx&logoColor=white)
![Google Cloud Run](https://img.shields.io/badge/Google%20Cloud%20Run-deployed-4285F4?logo=googlecloud&logoColor=white)
![Cloudflare](https://img.shields.io/badge/Cloudflare-DNS%20%2B%20proxy-F38020?logo=cloudflare&logoColor=white)
![License](https://img.shields.io/github/license/CJhangTW/personal-link-hub)
![GitHub last commit](https://img.shields.io/github/last-commit/CJhangTW/personal-link-hub)

一個以 Django 建立的單體式個人網站導航頁。首頁展示個人介紹與連結清單，管理者可以透過 Django Admin 更新內容；每個連結也可以使用短網址轉址並累計點擊次數。

這個專案的應用程式與部署環境分離設計：Django 不依賴特定雲端服務，資料庫、容器映像儲存庫、執行平台與 DNS 供應商都可以依需求替換。

## 功能

- 單頁式個人網站首頁。
- 透過 Django Admin 管理個人資料與公開連結。
- 使用 `/r/<slug>/` 提供 HTTP 302 短網址轉址。
- 記錄連結點擊總數與最後點擊時間。
- 不保存原始 IP、User-Agent 或逐筆訪客事件。
- `/healthz/` 健康檢查端點，方便容器與雲端平台使用。
- 支援 PostgreSQL，也可以在測試或簡單本機情境使用其他 Django 支援的資料庫設定。
- 具備 Dockerfile 與 Docker Compose 設定，可在本機或雲端執行。

## 技術組成

- Python 3.12
- Django 5.2
- `uv`：Python 依賴與虛擬環境管理
- PostgreSQL：建議的正式環境資料庫
- Gunicorn：正式環境 WSGI 伺服器
- WhiteNoise：提供 Django 靜態檔案
- Docker：建立可攜式應用程式映像檔
- Docker Compose：本機同時啟動 Django、PostgreSQL 與 Nginx

資料庫不綁定特定供應商。你可以使用本機 PostgreSQL、自建伺服器，或任一提供 PostgreSQL 連線字串的託管服務。應用程式透過 `DATABASE_URL` 連線。

## 網址

| 路徑 | 用途 |
| --- | --- |
| `/` | 公開個人網站導航頁 |
| `/r/<slug>/` | 將短網址轉址到設定的目標 URL |
| `/healthz/` | 服務健康檢查 |
| `/admin/` | Django Admin 管理頁 |

## 專案結構

```text
.
├── config/              # Django 專案設定、URL 與 WSGI
├── links/               # 個人資料、連結模型、首頁與短網址功能
├── deploy/              # 部署與自訂網域參考文件
├── compose.yaml         # 本機 Docker Compose 服務
├── Dockerfile           # 應用程式容器映像檔
├── nginx.conf           # 本機反向代理與靜態檔案設定
├── pyproject.toml       # Python 專案與依賴宣告
└── uv.lock              # 鎖定依賴版本
```

## 本機開發方式

### 方式一：使用 Docker Desktop 與 Docker Compose

這是最接近正式容器環境的本機方式。Docker Desktop 需要包含 Docker Compose 外掛。

1. 建立本機環境變數檔：

   ```powershell
   Copy-Item .env.example .env
   ```

2. 編輯 `.env`，至少替換 `SECRET_KEY` 與 `POSTGRES_PASSWORD`。

3. 建立並啟動服務：

   ```powershell
   docker compose up --build
   ```

   Compose 會啟動：

   - `db`：PostgreSQL
   - `web`：Django、migration、collectstatic 與 Gunicorn
   - `nginx`：本機反向代理，對外提供 `http://localhost/`

4. 建立 Django Admin 管理者：

   ```powershell
   docker compose exec web python manage.py createsuperuser
   ```

5. 開啟網站：

   - 首頁：<http://localhost/>
   - 管理頁：<http://localhost/admin/>

停止服務：

```powershell
docker compose down
```

若要連同本機 PostgreSQL 資料一起刪除，才使用 `docker compose down -v`。這只會影響本機 Compose volume。

### 方式二：使用 uv 在主機執行 Django

這種方式適合快速開發或執行測試；你仍需要準備一個可連線的資料庫。

```powershell
uv sync
Copy-Item .env.example .env
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

預設開發網址是 <http://127.0.0.1:8000/>。若使用本機 PostgreSQL，請在 `.env` 設定正確的 `DATABASE_URL`；若使用託管 PostgreSQL，請使用該服務提供的連線字串。

## Docker 與 Docker Hub 的關係

Docker Desktop 是本機的容器工具，不等於 Docker Hub。這個專案目前的使用方式如下：

| 項目 | 目前用途 |
| --- | --- |
| Docker Desktop | 在本機建置、啟動與測試容器 |
| `Dockerfile` | 建立本專案的 Django/Gunicorn 應用程式映像檔 |
| Docker Compose | 本機編排 Django、PostgreSQL 與 Nginx |
| Docker Hub | 目前沒有推送本專案自己的映像檔 |
| 基礎映像檔 | 建置時會從公開 registry 取得，例如 `python:3.12-slim`、`postgres:16-alpine` 與 `nginx:1.27-alpine` |

因此，現在不需要執行 `docker login`、`docker tag` 或 `docker push` 到 Docker Hub。只有在你選擇 Docker Hub 作為映像檔儲存庫時，才需要把自己的應用程式映像檔推送上去。

容器映像檔可以放在任何支援 OCI/Docker 映像格式的 registry，例如：

- Google Artifact Registry
- GitHub Container Registry
- Docker Hub
- 其他私有 registry

基本映像檔流程如下，實際的 registry 網址依部署平台而定：

```powershell
docker build --tag personal-link-hub:local .
docker run --rm -p 8080:8080 `
  -e SECRET_KEY=local-only `
  -e ALLOWED_HOSTS=localhost,127.0.0.1 `
  -e DATABASE_URL=postgresql://user:password@host:5432/database `
  personal-link-hub:local
```

正式環境不要把密碼、`SECRET_KEY` 或 `DATABASE_URL` 寫入 Dockerfile、映像檔或 Git。請使用部署平台的 Secret 管理功能或安全的環境變數設定。

## 環境變數

請以 `.env.example` 為起點建立 `.env`。`.env` 僅供本機使用，不應提交到 Git。

| 變數 | 用途 |
| --- | --- |
| `DEBUG` | 開發環境通常為 `1`，正式環境應為 `0` |
| `SECRET_KEY` | Django 加密與安全設定，正式環境必須使用隨機且保密的值 |
| `ALLOWED_HOSTS` | 允許的 Host 名稱，使用逗號分隔 |
| `CSRF_TRUSTED_ORIGINS` | 正式 HTTPS 網域，例如 `https://links.example.com` |
| `DATABASE_URL` | PostgreSQL 或其他設定的資料庫連線字串 |
| `POSTGRES_DB` | Docker Compose PostgreSQL 資料庫名稱 |
| `POSTGRES_USER` | Docker Compose PostgreSQL 使用者名稱 |
| `POSTGRES_PASSWORD` | Docker Compose PostgreSQL 密碼 |

正式部署時，`ALLOWED_HOSTS` 與 `CSRF_TRUSTED_ORIGINS` 必須包含實際對外使用的網域。若使用自訂網域，DNS、TLS 憑證與反向代理設定也必須由對應的平台完成。

## 測試與檢查

使用 `uv` 執行 Django 系統檢查與測試：

```powershell
uv run python manage.py check
uv run python manage.py test
```

正式部署前建議執行：

```powershell
uv run python manage.py check --deploy
uv run python manage.py collectstatic --noinput
uv run python manage.py migrate
```

## 部署概念

任何支援容器的服務都可以依照以下流程部署：

```text
Dockerfile
    ↓ docker build
Container registry
    ↓ deploy image
Container runtime
    ↓ runtime secrets and environment variables
Django + Gunicorn
    ↓ DATABASE_URL
PostgreSQL
```

部署平台可以是 Cloud Run、VPS、Kubernetes、其他容器平台或自建伺服器。平台選擇不會改變 Django 應用程式的核心功能。

本專案另有目前部署環境的參考文件：

- [`deploy/README.md`](deploy/README.md)：容器映像、Cloud Run、Secret、Cloudflare 自訂網域與 URL 設定範例
- [`deploy/GITHUB.md`](deploy/GITHUB.md)：本專案的 GitHub 與線上服務說明
- [`TESTING.md`](TESTING.md)：本機與部署前測試流程

## 自訂網域與 URL 設定

應用程式本身只負責回應 HTTP 路徑；自訂網域的 DNS、TLS 憑證與反向代理則由部署平台或 DNS/CDN 服務處理。

若將服務綁定到 `links.example.com`，通常需要：

1. 在部署平台建立服務的自訂網域設定。
2. 依平台要求在 DNS 供應商新增 CNAME、A 或驗證用 TXT 記錄。
3. 將 `links.example.com` 加入 `ALLOWED_HOSTS`。
4. 將 `https://links.example.com` 加入 `CSRF_TRUSTED_ORIGINS`。
5. 確認 `/healthz/`、`/` 與 `/r/<slug>/` 都能透過 HTTPS 正常存取。

Cloudflare 可以作為 DNS、代理與 TLS 服務，但不是本專案的必要依賴。相同設定也可以使用其他 DNS 或 CDN 服務完成。

## 隱私與資料保存

每次成功短網址轉址只會更新對應 `LinkItem` 的：

- `click_count`
- `last_clicked_at`

本專案不建立逐筆點擊事件資料表，也不在 Django 資料庫保存原始 IP、User-Agent 或其他訪客識別資料。若需要瀏覽器、裝置或來源分析，應由目標網站或獨立分析服務負責。

## 授權

本專案採用 [MIT License](LICENSE)。你可以自由使用、修改與發布本專案，但需要保留原作者與授權聲明。

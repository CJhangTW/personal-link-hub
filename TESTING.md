# Testing guide

這個專案建議分五層測試。先從本機快速測試開始，再測 Docker image，最後才測 Neon／Cloud Run。

## 1. 快速 Django 測試

這些測試不需要啟動 Docker，也不應連到正式 Neon。使用暫存 SQLite：

```powershell
$env:DATABASE_URL = "sqlite:///C:/Temp/personal-link-hub-test.sqlite3"
$env:DEBUG = "1"

uv sync --locked
uv lock --check
uv run python manage.py check
uv run python manage.py test
```

目前測試涵蓋：

- SiteProfile 可以保存 Admin 編輯內容
- 非 HTTP(S) URL 會被拒絕
- slug 不可重複
- 首頁只顯示可見連結並依排序排列
- `/healthz/` 回傳 200
- 短網址回傳 302 且增加點擊總數
- 隱藏／不存在連結回傳 404
- 未登入使用者不能進入 Admin

預期結果：

```text
Ran 9 tests ... OK
System check identified no issues
```

## 2. 測試 Neon 設定

Neon 只需要確認設定與 migration，不要直接對 Neon 執行一般測試套件；Django test runner 會建立並刪除 test database，而 pooled connection 可能讓刪除動作被其他連線阻擋。

```powershell
uv run python manage.py check
uv run python manage.py showmigrations
uv run python manage.py migrate --plan
```

看到 `links.0001_initial` 和其他 Django migrations 已套用即可。第一次正式建立資料表才執行：

```powershell
uv run python manage.py migrate --noinput
```

不要把 `DATABASE_URL` 印到終端機或提交到 Git。`.env` 只能放在本機，正式環境使用 Secret Manager。

## 3. 手動測試 Django 頁面

建立 Admin 帳號：

```powershell
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

依序測試：

1. 開啟 `http://127.0.0.1:8000/`
2. 開啟 `http://127.0.0.1:8000/admin/`
3. 修改 SiteProfile，重新整理首頁，確認名稱與標題更新
4. 建立 LinkItem，例如 slug `portfolio`
5. 確認首頁顯示 `/r/portfolio/`
6. 點擊連結，確認瀏覽器被導向 target URL
7. 回到 Admin，確認 `click_count` 增加
8. 將 `is_visible` 設為 False，確認首頁不再顯示且短網址回傳 404

## 4. Docker image 測試

先確認 Docker Desktop 已啟動：

```powershell
docker info
```

建立 image：

```powershell
docker build --tag personal-link-hub:verification .
```

啟動 container：

```powershell
docker run --detach `
  --name personal-link-hub-verification `
  --publish 18080:8080 `
  --env-file .env `
  --env DEBUG=0 `
  --env SECRET_KEY=verification-only-long-secret-with-more-than-fifty-characters-123 `
  --env ALLOWED_HOSTS=localhost,127.0.0.1 `
  personal-link-hub:verification
```

因為 production 設定會強制 HTTPS，直接使用 HTTP 看到 301 是正常的。用 Cloud Run 會加入的 header 模擬 HTTPS：

```powershell
curl.exe --noproxy "*" -H "X-Forwarded-Proto: https" http://127.0.0.1:18080/healthz/
curl.exe --noproxy "*" -H "X-Forwarded-Proto: https" -I http://127.0.0.1:18080/static/links/style.css
curl.exe --noproxy "*" -H "X-Forwarded-Proto: https" -I http://127.0.0.1:18080/
```

預期結果：

```text
/healthz/                 200
/static/links/style.css   200
/                         200
```

查看 container 啟動問題：

```powershell
docker logs personal-link-hub-verification
docker rm --force personal-link-hub-verification
```

## 5. Docker Compose 測試

Compose 會啟動本機 PostgreSQL、Django 和 Nginx：

```powershell
docker compose --env-file .env.example up --build
```

Compose 的每個指令都要保留 `--env-file .env.example`，因為本機 `.env` 是
Neon 設定，不包含 local PostgreSQL 的 `POSTGRES_PASSWORD`：

```powershell
docker compose --env-file .env.example exec web python manage.py createsuperuser
```

開另一個終端機測試：

```powershell
curl.exe -I http://127.0.0.1/healthz/
curl.exe -I http://127.0.0.1/static/links/style.css
curl.exe -I http://127.0.0.1/
```

如果 web container 反覆重啟並看到：

```text
Failed to initialize cache at `/nonexistent/.cache/uv`
```

代表使用了舊版 Compose command，讓非 root 的 `app` 使用者在 runtime 執行
`uv run`。目前 Compose 會直接呼叫 image 內的 `python` 與 `gunicorn`，因此
請重新建置：

```powershell
docker compose --env-file .env.example down
docker compose --env-file .env.example up --build
```

結束並清理本機服務：

```powershell
docker compose --env-file .env.example down
```

若要連同本機 PostgreSQL volume 一起刪除，才使用
`docker compose --env-file .env.example down --volumes`；這會刪除本機資料庫資料，
不要對正式 Neon 使用類似操作。

## 6. Cloud Run 上線後測試

部署完成後先取得服務網址：

```powershell
gcloud run services describe personal-link-hub `
  --region asia-east1 `
  --format="value(status.url)"
```

使用服務網址測試：

```powershell
curl.exe -I https://SERVICE_URL/healthz/
curl.exe -I https://SERVICE_URL/
curl.exe -I https://SERVICE_URL/r/portfolio/
```

應確認：

- `/healthz/` 回傳 200
- `/` 回傳 200
- `/r/portfolio/` 回傳 302
- `Location` 是設定的 target URL
- Admin 可以登入
- Neon 的 `click_count` 有增加
- Cloud Run logs 沒有 database connection error

查看 logs：

```powershell
gcloud run services logs read personal-link-hub --region asia-east1 --limit 50
```

## 7. Cloudflare custom domain 測試

假設你使用 `links.example.com`。在 Cloud Run domain mapping 建立後，先確認
Cloud Run 回傳的 DNS records 都已經加到 Cloudflare。驗證期間，Google 要求的
TXT／CNAME records 應保持 DNS-only（灰雲）；網頁 CNAME 也先保持灰雲，等憑證
啟用後再切成 Proxied（橘雲）。

```powershell
gcloud beta run domain-mappings describe `
  --domain links.example.com `
  --region asia-east1

Resolve-DnsName links.example.com
curl.exe -I https://links.example.com/healthz/
curl.exe -I https://links.example.com/
curl.exe -I https://links.example.com/r/portfolio/
```

預期結果：

- `/healthz/` 和 `/` 回傳 200
- `/r/portfolio/` 回傳 302，`Location` 是設定的 target URL
- Cloudflare SSL/TLS 使用 `Full (strict)`
- 不會出現 HTTP/HTTPS redirect loop
- Django 的 `ALLOWED_HOSTS` 包含自訂網域
- Django 的 `CSRF_TRUSTED_ORIGINS` 使用完整的 `https://` origin

若 Cloudflare 回傳 `526`，先檢查 Cloudflare-to-origin 的 SSL 憑證與
`Full (strict)` 設定；若 Cloud Run mapping 長時間無法完成，先把 Cloudflare
`Always Use HTTPS` 關閉並保持 DNS-only，待 Google 憑證完成後再開啟代理。

## 測試時的資料安全原則

- 自動測試使用 SQLite 或本機 PostgreSQL。
- Neon 只執行 migration、唯讀檢查與少量手動驗證。
- 不要把 production `DATABASE_URL` 放在測試 log。
- 不要用 `docker compose --env-file .env.example down --volumes` 清理正式資料。
- 部署前重新產生曾經貼出或分享過的 Neon 密碼。
- Docker Hub image 不要包含 `.env`、Neon URL、Secret Manager 值或其他 secrets。

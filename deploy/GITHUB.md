# GitHub 與線上服務

本專案是「個人網站導航頁」，使用 Django 單體式架構管理個人資料與短網址。

## 線上架構

- Docker 建立 Django／Gunicorn 應用程式映像。
- 映像推送至 Google Artifact Registry。
- Google Cloud Run 對外執行服務，使用 HTTPS 與自動擴縮。
- Neon PostgreSQL 保存線上資料庫內容。
- Cloudflare 管理 DNS 與自訂網域。

## URL 設定

- 公開首頁：`/`
- 短網址轉址：`/r/<slug>/`
- Django 管理後台：`/admin/`
- Cloud Run 自訂網域：`https://links.cjhang.com/`

Cloudflare 的 `links` DNS 記錄使用 DNS-only，CNAME 指向 `ghs.googlehosted.com`，由 Cloud Run Domain Mapping 配置自動 HTTPS 憑證。應用程式的 `ALLOWED_HOSTS` 與 `CSRF_TRUSTED_ORIGINS` 必須同時包含 Cloud Run 網址及正式自訂網域。

## 敏感設定

Neon 連線字串與 Django `SECRET_KEY` 不放進 Git、Docker image 或公開 README；正式環境使用 Google Secret Manager 注入 Cloud Run。

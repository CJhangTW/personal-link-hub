# Cloud Run deployment notes

This directory documents the production deployment boundary. The application image is built from the repository root and stored in Artifact Registry. Cloud Run runs Django/Gunicorn directly, with WhiteNoise serving collected static files; `nginx` remains local-only in `compose.yaml`.

Required runtime secrets:

- `SECRET_KEY`: a long random Django secret
- `DATABASE_URL`: Neon pooled PostgreSQL URL with `sslmode=require`

Required runtime variables:

- `DEBUG=0`
- `ALLOWED_HOSTS`: the Cloud Run hostname or custom domain
- `CSRF_TRUSTED_ORIGINS`: HTTPS origins for the hostname or custom domain

Recommended initial limits for a personal service:

- Cloud Run min instances: `0`
- Cloud Run max instances: `3`
- Cloud Run container port: `8080`
- Neon Free plan scale-to-zero enabled

## Docker Hub alternative

Docker Hub can be used as the image registry instead of Artifact Registry. For
this project, use a public repository only if you are comfortable with the
application source being extractable from the image. Keep secrets out of the
image; runtime secrets still belong in Secret Manager.

```powershell
$DOCKERHUB_USER = "your-dockerhub-user"
$IMAGE = "docker.io/$DOCKERHUB_USER/personal-link-hub:2026-07-19-01"

docker login
docker build --tag $IMAGE .
docker push $IMAGE

gcloud run deploy personal-link-hub `
  --image $IMAGE `
  --region asia-east1 `
  --port 8080 `
  --allow-unauthenticated `
  --max 3 `
  --set-env-vars "^@^DEBUG=0@ALLOWED_HOSTS=SERVICE_URL_OR_DOMAIN@CSRF_TRUSTED_ORIGINS=https://SERVICE_URL_OR_DOMAIN" `
  --set-secrets "SECRET_KEY=django-secret-key:1,DATABASE_URL=database-url:1"
```

Use an immutable version tag, or preferably deploy the image by digest after
checking it. Avoid reusing `latest` for production rollouts.

Google Cloud recommends Artifact Registry for higher availability and supply
chain control. Docker Hub is convenient for learning and a low-traffic
personal project, but Docker Hub pull limits and external-registry availability
are additional operational considerations.

## Custom domain with Cloudflare

Use a subdomain such as `links.example.com` first. The simplest setup is:

```text
Browser
  -> Cloudflare DNS + proxy + HTTPS
  -> Cloud Run custom-domain mapping
  -> personal-link-hub service
```

Cloud Run domain mapping is easy to learn but currently has Preview and
production limitations. Google recommends a global external Application Load
Balancer for a production-grade custom domain. For this personal project,
Cloud Run domain mapping is a reasonable first deployment; move to the load
balancer route if you later need advanced routing, Cloud Armor, or stricter TLS
control.

After the Cloud Run service is deployed:

1. Verify the base domain in Google Search Console if Google requests domain
   ownership verification.
2. Create the mapping:

   ```powershell
   gcloud beta run domain-mappings create `
     --service personal-link-hub `
     --domain links.example.com `
     --region asia-east1
   ```

3. Get the DNS records Cloud Run requires:

   ```powershell
   gcloud beta run domain-mappings describe `
     --domain links.example.com `
     --region asia-east1
   ```

4. In Cloudflare DNS, add every `resourceRecords` entry shown by Cloud Run.
   Keep validation records, especially TXT records, DNS-only (grey cloud).
   Temporarily keep the web CNAME DNS-only while Google validates the mapping
   and provisions its certificate.
5. In Cloudflare SSL/TLS, select `Full (strict)`. Do not use `Flexible` because
   this application redirects HTTP to HTTPS in production.
6. After the Cloud Run certificate is active, turn on the orange proxy for
   the web hostname. If Google validation is stuck, temporarily turn off
   Cloudflare `Always Use HTTPS` and retry validation.

Set the Cloud Run runtime variables to include the custom domain:

```text
DEBUG=0
ALLOWED_HOSTS=links.example.com,SERVICE_HASH-REGION.a.run.app
CSRF_TRUSTED_ORIGINS=https://links.example.com
```

Because `ALLOWED_HOSTS` contains a comma, use a custom gcloud delimiter when
setting both the custom domain and the generated Cloud Run hostname:

```powershell
gcloud run services update personal-link-hub `
  --region asia-east1 `
  --set-env-vars "^@^DEBUG=0@ALLOWED_HOSTS=links.example.com,SERVICE_HASH-REGION.a.run.app@CSRF_TRUSTED_ORIGINS=https://links.example.com"
```

Keep the `run.app` hostname during the transition so it remains available for
diagnostics. If you also serve `www.example.com`, add it to both variables and
create a second domain mapping or redirect rule deliberately.

Verify both the custom domain and the Cloud Run URL:

```powershell
curl.exe -I https://links.example.com/healthz/
curl.exe -I https://links.example.com/
curl.exe -I https://SERVICE_HASH-REGION.a.run.app/healthz/
```

Expected results are `200` for `/healthz/` and `/`, plus a valid HTTPS
certificate and no redirect loop. A `526` from Cloudflare usually means the
Cloudflare-to-origin certificate or SSL mode is not configured correctly.

Run `python manage.py migrate` as a release step before moving traffic to a new revision. Do not put the Neon connection string in this directory or in the Docker image.

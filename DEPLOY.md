# Deploying the backend to Railway

Target: **Django + Postgres + Redis + Celery**, one repo, three services plus two managed addons. HTTPS is handled by Railway's edge — no nginx, no self-signed certs.

## One-time setup

1. Sign in at [railway.app](https://railway.app) and create a new project → **Deploy from GitHub repo** → pick this repo.
2. When prompted, choose the `Dockerfile` builder. Railway will pick up `railway.json`.
3. In the project, click **New → Database → Postgres**. Wait for it to provision.
4. Click **New → Database → Redis**. Wait for it to provision.

Your project now has three items: the web app + Postgres + Redis. You'll add two more services next.

## Web service (the default one Railway created)

1. Go to the web service → **Variables** → paste everything from `.env.production.example`.
   - For the `${{ Postgres.PGHOST }}` etc. references, use Railway's variable picker (autocompletes once Postgres is in the project).
   - For `CORS_ALLOWED_ORIGINS` and `SITE_URL`, use your Vercel URL once the frontend is deployed (placeholder for now).
2. **Settings → Networking → Public Networking → Generate Domain**. You get something like `mar-hotels-backend-production.up.railway.app`.
3. Add that domain to `ALLOWED_HOSTS`.
4. Deploy.

The web service boots with `entrypoint.sh`, which runs `migrate` + `collectstatic` + creates the superuser, then starts `gunicorn` on `$PORT`.

## Celery worker service

1. **New → GitHub Repo** (pick the same repo). Railway uses the same Dockerfile.
2. **Variables**: copy all vars from the web service, then add:
   - `RUN_SETUP=false` (skip migrations/static — web handles that)
3. **Settings → Start Command**:
   ```
   celery -A hotel_booking worker -l info --concurrency=4 --max-tasks-per-child=1000
   ```
4. **Settings → Networking** → disable public networking (internal only).
5. Deploy.

## Celery beat service

1. **New → GitHub Repo** again.
2. Copy env vars + `RUN_SETUP=false`.
3. **Start Command**:
   ```
   celery -A hotel_booking beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```
4. Disable public networking.
5. Deploy.

## After first deploy — seed the DB

Railway CLI:
```bash
railway login
railway link                   # pick your project
railway service                # pick the web service
railway run bash               # opens a shell inside the container
cd /app/hotel_booking
python manage.py shell < seed_demo.py
```

Or from the Railway dashboard → web service → **Deploy Logs → Run command** → paste the shell command.

## Update the Vercel frontend

Once the Railway web service has a domain:
- In Vercel env: `VITE_API_BASE_URL=https://<your-railway-domain>/api/v1`
- Redeploy the frontend.

Then come back to Railway web service and fix:
- `ALLOWED_HOSTS=<railway-domain>,<vercel-domain>`
- `CORS_ALLOWED_ORIGINS=https://<vercel-domain>`
- `SITE_URL=https://<vercel-domain>`

Redeploy. Tap redirects now land on the real frontend.

## Expected monthly cost

- Web service (~512MB, light traffic): ~$3–5
- Celery worker: ~$2–3
- Celery beat: ~$1
- Postgres: ~$1–3
- Redis: ~$1

Total: **$8–13/mo** under normal demo traffic. Railway gives $5 free credit/mo so the effective bill is smaller.

## Gotchas

- **Migration folders are gitignored** in this repo. You must commit them before deploy, or add `python manage.py makemigrations` ahead of `migrate` in `entrypoint.sh`. Easiest fix: remove `**/migrations/` from `.gitignore` and commit the existing migration files locally generated.
- **Register API auto-verifies in DEBUG only**. In production you need a real email backend so `send_verification_email` can actually deliver.
- **Tap webhooks** (`/api/v1/payments/callback/`) need to be registered in the Tap dashboard pointing at your Railway domain.
- **Static files** are served by WhiteNoise (already in `MIDDLEWARE`), so you don't need S3 for the demo.
- **Media uploads** (user avatars, offer images) need persistent storage. For a demo, Railway's ephemeral volume is fine. For production, add S3 via `django-storages`.

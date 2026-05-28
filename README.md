# Job Board — FastAPI + React + Telegram + Railway

A small but production-shaped job board:

| Side          | Stack                                                         | Service in Railway        |
| ------------- | ------------------------------------------------------------- | ------------------------- |
| Backend + Bot | FastAPI · SQLAlchemy 2 · asyncpg · redis-py · **aiogram 3**   | `backend/`                |
| Public web    | Vite · React · TypeScript · Tailwind                          | `frontend-public/`        |
| Admin web     | Vite · React · TypeScript · Tailwind                          | `frontend-admin/`         |
| Database      | PostgreSQL (Railway template)                                 | plugin                    |
| Cache/Bus     | Redis (Railway template)                                      | plugin                    |

Total Railway resources: **3 services + 2 plugins = 5** (fits the Trial plan limit).

No Docker — everything runs on Railway via **Nixpacks** (each service has `nixpacks.toml`, `Procfile`, and `railway.json`).

The Telegram bot runs **in-process** with the FastAPI backend as a background asyncio task (started/stopped via the lifespan handler). It talks to Postgres directly through the same SQLAlchemy session factory the API uses — no internal HTTP loop, no extra service to deploy. Set `BOT_TOKEN` to enable it; leave it empty to disable.

---

## What it does

**Public (`frontend-public`)**
- Browse open roles with title / company / location / salary / description
- Apply with full name, email, optional cover letter
- Confirmation email is sent via Resend
- Friendly empty / loading / error states, mobile-responsive

**Admin (`frontend-admin`)**
- Password sign-in (JWT, no registration)
- CRUD for jobs (title, company, location, description, salary, status `open`/`closed`)
- View all applications, filter by job, click-to-email applicants

**Telegram bot (lives inside `backend/app/bot/`)**
- Whitelist by `ADMIN_TG_IDS` env var
- Persistent menu: Jobs / New job / Applications / Help
- Conversational job creation (FSM): title → company → location → description → salary → confirm
- Inline buttons per job: close/reopen, view applicants, delete (with confirmation)
- Real-time push: every new application is announced in chat to all admins via Redis Pub/Sub
- Runs as an asyncio task started from the FastAPI lifespan — no separate Railway service required

**Backend (`backend`)**
- Public endpoints: `GET /api/jobs`, `GET /api/jobs/{id}`, `POST /api/jobs/{id}/apply`
- Admin endpoints: `POST /api/admin/login`, full CRUD for jobs, list applications
- OpenAPI docs at `/docs`

---

## How Postgres + Redis are used (meaningfully)

- **Postgres** — source of truth for `jobs` and `applications` (with FK + cascade delete + indexes).
- **Redis** is used in three different ways:
  1. **Cache** — `GET /api/jobs` is cached as `jobs:list:open` with a 60s TTL. Any admin write invalidates the key immediately.
  2. **Rate limiting** — a key like `rl:apply:{job_id}:{email}` blocks duplicate applications for 1 hour.
  3. **Pub/Sub** — backend publishes `applications:new` events; the Telegram bot subscribes and pushes them to admins. Fully decoupled — backend never talks to Telegram directly.

---

## Local run (3 terminals)

```bash
# 1 — Postgres + Redis (use any local install, brew, or docker run)
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/jobboard
# REDIS_URL=redis://localhost:6379

# 2 — backend (+ telegram bot, if BOT_TOKEN is set)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # DATABASE_URL, REDIS_URL, ADMIN_PASSWORD, JWT_SECRET, BOT_TOKEN, ADMIN_TG_IDS, ...
uvicorn app.main:app --reload
# → http://localhost:8000/docs

# 3 — public site
cd frontend-public
npm install
cp .env.example .env       # VITE_API_URL=http://localhost:8000
npm run dev                # → http://localhost:5173

# 4 — admin site
cd frontend-admin
npm install
cp .env.example .env
npm run dev                # → http://localhost:5174
```

> ⚠️ When running with `--reload`, uvicorn restarts the whole process on every code change, which means the bot restarts too. Telegram's `getUpdates` long-polling sometimes returns a 409 conflict if two pollers race for a few seconds — just wait. In production (no reload) this never happens.

---

## Railway deployment (no Docker)

1. **Create a new project** on Railway and connect this Git repository.
2. **Add plugins** from the marketplace:
   - **PostgreSQL** → exposes `DATABASE_URL`
   - **Redis** → exposes `REDIS_URL`
3. **Create 3 services** from the same repo, each with its own **Root Directory**:
   - `backend/`
   - `frontend-public/`
   - `frontend-admin/`

   Each folder already contains `nixpacks.toml`, `Procfile`, and `railway.json` — Railway will pick them up automatically.
4. **Generate public domains** for all three services (Settings → Networking → Generate Domain).
5. **Set environment variables** (`Variables` tab) using Railway's reference syntax `${{Postgres.DATABASE_URL}}` / `${{Redis.REDIS_URL}}`:

   **backend** (the Telegram bot lives here too)
   ```
   DATABASE_URL=${{Postgres.DATABASE_URL}}
   REDIS_URL=${{Redis.REDIS_URL}}
   ADMIN_PASSWORD=<your-strong-password>
   JWT_SECRET=<random-32+chars>
   RESEND_API_KEY=<from resend.com>
   RESEND_FROM=Job Board <onboarding@resend.dev>
   CORS_ORIGINS=https://<frontend-public-domain>,https://<frontend-admin-domain>
   # Optional — only set these if you want the Telegram bot enabled
   BOT_TOKEN=<from @BotFather>
   ADMIN_TG_IDS=11111111,22222222
   ```

   **frontend-public** & **frontend-admin**
   ```
   VITE_API_URL=https://<backend-domain>
   ```
   Vite needs the env at **build** time, so a redeploy is required after changing it.

6. **Deploy**. Backend will auto-create tables on first boot via SQLAlchemy. If `BOT_TOKEN` is set, the bot starts as a background task inside the same worker.

The `backend` service has a healthcheck at `/api/health`. Frontends are static Vite builds served by `serve`.

### Note on Railway resource limits

Railway's Trial plan caps a project at **5 resources**. This setup uses exactly that — 3 services (`backend`, `frontend-public`, `frontend-admin`) + 2 plugins (`Postgres`, `Redis`). If you'd rather run the bot as a 4th dedicated service, just upgrade to Hobby ($5/mo); the bot code in `backend/app/bot/` is self-contained and easy to lift out.

---

## API quick tour

```bash
# Public
curl https://<backend>/api/jobs
curl https://<backend>/api/jobs/1
curl -X POST https://<backend>/api/jobs/1/apply \
     -H 'Content-Type: application/json' \
     -d '{"full_name":"Jane","email":"jane@example.com","cover_letter":"hi"}'

# Admin
TOKEN=$(curl -s -X POST https://<backend>/api/admin/login \
              -H 'Content-Type: application/json' \
              -d '{"password":"..."}' | jq -r .access_token)

curl https://<backend>/api/admin/jobs -H "Authorization: Bearer $TOKEN"
```

OpenAPI: **`https://<backend>/docs`**

---

## What I'd improve next

- **File uploads** for résumés (S3-compatible storage; Railway has volumes for objects).
- **Resend webhooks** to track delivery / bounce of confirmation emails.
- **Search & filters** on the public board (Postgres full-text or Meilisearch plugin).
- **Application statuses** (new / reviewed / hired / rejected) with audit trail.
- **2FA / proper SSO** for admin sign-in (currently a single shared password — fine for a demo, not for production).
- **Tests**: pytest + httpx for backend, Vitest + Playwright for the frontends.
- **Refresh tokens** for admin JWTs and a server-side blocklist in Redis.
- **Telegram bot polish**: pagination for long lists, edit existing jobs in chat, search by title.
- **Observability**: Sentry SDK on every service, structured logging, Railway log drains.

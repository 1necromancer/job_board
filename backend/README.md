# Job Board — Backend (FastAPI)

## Local run

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in DATABASE_URL, REDIS_URL, ADMIN_PASSWORD, JWT_SECRET
uvicorn app.main:app --reload
```

OpenAPI: http://localhost:8000/docs

## Migrations (optional)

Tables are auto-created via SQLAlchemy on startup. For controlled migrations:

```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## Railway

- Builder: Nixpacks (`nixpacks.toml`)
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Healthcheck: `/api/health`
- Environment: `DATABASE_URL`, `REDIS_URL` (auto from plugins), `ADMIN_PASSWORD`, `JWT_SECRET`, `RESEND_API_KEY`, `CORS_ORIGINS`

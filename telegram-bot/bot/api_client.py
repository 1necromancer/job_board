import asyncio
import logging
from typing import Any

import httpx

from bot.config import get_settings

logger = logging.getLogger(__name__)


class BackendClient:
    """Thin wrapper around the FastAPI admin API.

    Logs in once with ADMIN_PASSWORD and refreshes the JWT on 401.
    """

    def __init__(self) -> None:
        s = get_settings()
        self._base = s.BACKEND_URL.rstrip("/")
        self._password = s.ADMIN_PASSWORD
        self._client = httpx.AsyncClient(base_url=self._base, timeout=15)
        self._token: str | None = None
        self._lock = asyncio.Lock()

    async def close(self) -> None:
        await self._client.aclose()

    async def _login(self) -> None:
        r = await self._client.post(
            "/api/admin/login", json={"password": self._password}
        )
        r.raise_for_status()
        self._token = r.json()["access_token"]

    async def _ensure_token(self) -> None:
        if self._token is None:
            async with self._lock:
                if self._token is None:
                    await self._login()

    async def _request(self, method: str, path: str, **kw) -> httpx.Response:
        await self._ensure_token()
        headers = kw.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._token}"
        r = await self._client.request(method, path, headers=headers, **kw)
        if r.status_code == 401:
            async with self._lock:
                await self._login()
            headers["Authorization"] = f"Bearer {self._token}"
            r = await self._client.request(method, path, headers=headers, **kw)
        return r

    async def list_jobs(self) -> list[dict[str, Any]]:
        r = await self._request("GET", "/api/admin/jobs")
        r.raise_for_status()
        return r.json()

    async def create_job(self, payload: dict[str, Any]) -> dict[str, Any]:
        r = await self._request("POST", "/api/admin/jobs", json=payload)
        r.raise_for_status()
        return r.json()

    async def update_job(self, job_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        r = await self._request("PATCH", f"/api/admin/jobs/{job_id}", json=payload)
        r.raise_for_status()
        return r.json()

    async def delete_job(self, job_id: int) -> None:
        r = await self._request("DELETE", f"/api/admin/jobs/{job_id}")
        r.raise_for_status()

    async def list_applications(self, job_id: int | None = None) -> list[dict[str, Any]]:
        params = {"job_id": job_id} if job_id is not None else None
        r = await self._request("GET", "/api/admin/applications", params=params)
        r.raise_for_status()
        return r.json()


backend = BackendClient()

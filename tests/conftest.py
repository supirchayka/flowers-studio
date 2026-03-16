from __future__ import annotations

import hashlib
import hmac
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(ROOT / 'tests' / 'studio_test.db').as_posix()}"
os.environ["ALLOW_SCHEMA_CREATE"] = "true"
os.environ["ALLOW_DEV_LOGIN"] = "true"
os.environ["DEBUG"] = "false"
os.environ["TELEGRAM_BOT_TOKEN"] = "000000:dev-token"
os.environ["AUTH_SECRET"] = "test-secret"
os.environ["ADMIN_TELEGRAM_IDS"] = "5000"
os.environ["TELEGRAM_ADMIN_CHAT_IDS"] = ""
os.environ["STUDIO_TIMEZONE"] = "Europe/Moscow"
os.environ["SLOT_STEP_MINUTES"] = "30"

from app.db.base import Base
from app.db.session import engine
from app.main import app


@pytest.fixture
async def reset_database():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture
async def client(reset_database):
    async with LifespanManager(app):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver") as http_client:
            yield http_client


def build_signed_init_data(
    telegram_id: int,
    *,
    first_name: str,
    last_name: str | None = None,
    username: str | None = None,
) -> str:
    payload = {
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "auth_date": str(int(time.time())),
        "user": json.dumps(
            {
                "id": telegram_id,
                "first_name": first_name,
                "last_name": last_name,
                "username": username,
                "language_code": "ru",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", os.environ["TELEGRAM_BOT_TOKEN"].encode("utf-8"), hashlib.sha256).digest()
    signature = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    payload["hash"] = signature
    return urlencode(payload)


async def _auth_headers(client: AsyncClient, telegram_id: int, first_name: str) -> dict[str, str]:
    init_data = build_signed_init_data(telegram_id, first_name=first_name, username=f"user{telegram_id}")
    response = await client.post("/api/v1/auth/session", json={"init_data": init_data})
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def user_headers(client: AsyncClient) -> dict[str, str]:
    return await _auth_headers(client, 1001, "Client")


@pytest.fixture
async def second_user_headers(client: AsyncClient) -> dict[str, str]:
    return await _auth_headers(client, 1002, "Second")


@pytest.fixture
async def admin_headers(client: AsyncClient) -> dict[str, str]:
    return await _auth_headers(client, 5000, "Admin")

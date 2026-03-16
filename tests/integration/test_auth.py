import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode

import pytest


def build_signed_init_data() -> str:
    payload = {
        "query_id": "AAHdF6IQAAAAAN0XohDhrOrc",
        "auth_date": str(int(time.time())),
        "user": json.dumps(
            {
                "id": 12345,
                "first_name": "Auth",
                "username": "auth_user",
                "language_code": "ru",
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ),
    }
    data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(payload.items()))
    secret_key = hmac.new(b"WebAppData", os.environ["TELEGRAM_BOT_TOKEN"].encode("utf-8"), hashlib.sha256).digest()
    payload["hash"] = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
    return urlencode(payload)


@pytest.mark.asyncio
async def test_auth_session_validates_telegram_init_data(client):
    init_data = build_signed_init_data()

    response = await client.post("/api/v1/auth/session", json={"init_data": init_data})

    assert response.status_code == 200
    payload = response.json()
    assert payload["user"]["telegram_id"] == 12345
    assert payload["access_token"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {payload['access_token']}"})
    assert me.status_code == 200
    assert me.json()["first_name"] == "Auth"

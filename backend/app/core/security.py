from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import parse_qsl

from fastapi import HTTPException, status

from app.core.config import get_settings


@dataclass(slots=True)
class TelegramUserData:
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None
    language_code: str | None


@dataclass(slots=True)
class SessionTokenPayload:
    sub: int
    telegram_id: int
    exp: int


class TelegramInitDataValidator:
    def __init__(self, bot_token: str):
        self.bot_token = bot_token

    def validate(self, init_data: str) -> TelegramUserData:
        if not init_data:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="initData is required")

        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        signature = pairs.pop("hash", None)
        if not signature:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="initData hash is missing")

        data_check_string = "\n".join(f"{key}={value}" for key, value in sorted(pairs.items()))
        secret_key = hmac.new(b"WebAppData", self.bot_token.encode("utf-8"), hashlib.sha256).digest()
        calculated = hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calculated, signature):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="initData hash mismatch")

        auth_date = int(pairs.get("auth_date", "0"))
        auth_dt = datetime.fromtimestamp(auth_date, tz=UTC)
        if datetime.now(tz=UTC) - auth_dt > timedelta(days=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="initData expired")

        raw_user = pairs.get("user")
        if not raw_user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="initData user is missing")

        user = json.loads(raw_user)
        return TelegramUserData(
            telegram_id=int(user["id"]),
            first_name=user.get("first_name") or "Telegram user",
            last_name=user.get("last_name"),
            username=user.get("username"),
            language_code=user.get("language_code"),
        )


def _sign_bytes(data: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), data, hashlib.sha256).hexdigest()


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


def create_session_token(user_id: int, telegram_id: int) -> str:
    settings = get_settings()
    exp = int((datetime.now(tz=UTC) + timedelta(minutes=settings.session_ttl_minutes)).timestamp())
    payload = {"sub": user_id, "telegram_id": telegram_id, "exp": exp}
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    encoded = _b64_encode(raw)
    signature = _sign_bytes(encoded.encode("utf-8"), settings.auth_secret)
    return f"{encoded}.{signature}"


def decode_session_token(token: str) -> SessionTokenPayload:
    settings = get_settings()
    try:
        encoded, signature = token.split(".", maxsplit=1)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session token") from exc

    expected_signature = _sign_bytes(encoded.encode("utf-8"), settings.auth_secret)
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session signature")

    payload_raw = _b64_decode(encoded)
    payload: dict[str, Any] = json.loads(payload_raw.decode("utf-8"))
    if int(payload["exp"]) < int(datetime.now(tz=UTC).timestamp()):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")

    return SessionTokenPayload(
        sub=int(payload["sub"]),
        telegram_id=int(payload["telegram_id"]),
        exp=int(payload["exp"]),
    )


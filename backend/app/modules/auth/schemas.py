from pydantic import BaseModel, Field


class TelegramAuthRequest(BaseModel):
    init_data: str = Field(..., description="Raw Telegram Mini App initData string")


class DevLoginRequest(BaseModel):
    telegram_id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = "ru"


class UserRead(BaseModel):
    id: int
    telegram_id: int
    first_name: str
    last_name: str | None
    username: str | None
    is_admin: bool

    model_config = {"from_attributes": True}


class SessionResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


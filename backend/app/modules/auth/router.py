from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.dependencies import get_current_user
from app.db.models import User
from app.db.session import get_db
from app.modules.auth.schemas import DevLoginRequest, SessionResponse, TelegramAuthRequest, UserRead
from app.modules.auth.service import create_dev_session, create_session_for_init_data

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/session", response_model=SessionResponse)
async def auth_session(
    payload: TelegramAuthRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    settings = get_settings()
    return await create_session_for_init_data(session, payload.init_data, settings.telegram_bot_token)


@router.post("/dev-session", response_model=SessionResponse)
async def dev_session(
    payload: DevLoginRequest,
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SessionResponse:
    settings = get_settings()
    if not settings.allow_dev_login:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Dev login disabled")
    return await create_dev_session(session, payload)


@router.get("/me", response_model=UserRead)
async def auth_me(current_user: Annotated[User, Depends(get_current_user)]) -> UserRead:
    return UserRead.model_validate(current_user)

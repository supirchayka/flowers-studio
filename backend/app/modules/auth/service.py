from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import TelegramInitDataValidator, TelegramUserData, create_session_token
from app.db.models import User
from app.modules.auth.schemas import DevLoginRequest, SessionResponse, UserRead
from app.modules.users.service import upsert_telegram_user


async def create_session_for_init_data(session: AsyncSession, init_data: str, bot_token: str) -> SessionResponse:
    validator = TelegramInitDataValidator(bot_token)
    telegram_user = validator.validate(init_data)
    return await _create_session(session, telegram_user)


async def create_dev_session(session: AsyncSession, payload: DevLoginRequest) -> SessionResponse:
    telegram_user = TelegramUserData(
        telegram_id=payload.telegram_id,
        first_name=payload.first_name,
        last_name=payload.last_name,
        username=payload.username,
        language_code=payload.language_code,
    )
    return await _create_session(session, telegram_user)


async def _create_session(session: AsyncSession, telegram_user: TelegramUserData) -> SessionResponse:
    user = await upsert_telegram_user(session, telegram_user)
    await session.commit()
    await session.refresh(user)
    return _serialize_session(user)


def _serialize_session(user: User) -> SessionResponse:
    return SessionResponse(
        access_token=create_session_token(user.id, user.telegram_id),
        user=UserRead.model_validate(user),
    )


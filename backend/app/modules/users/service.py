from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.security import TelegramUserData
from app.db.models import User


async def upsert_telegram_user(session: AsyncSession, telegram_user: TelegramUserData) -> User:
    result = await session.execute(select(User).where(User.telegram_id == telegram_user.telegram_id))
    user = result.scalar_one_or_none()
    settings = get_settings()
    is_admin = telegram_user.telegram_id in settings.admin_telegram_ids

    if user is None:
        user = User(
            telegram_id=telegram_user.telegram_id,
            first_name=telegram_user.first_name,
            last_name=telegram_user.last_name,
            username=telegram_user.username,
            language_code=telegram_user.language_code,
            is_admin=is_admin,
        )
        session.add(user)
        await session.flush()
        return user

    user.first_name = telegram_user.first_name
    user.last_name = telegram_user.last_name
    user.username = telegram_user.username
    user.language_code = telegram_user.language_code
    user.is_admin = is_admin
    await session.flush()
    return user

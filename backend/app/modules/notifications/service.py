from __future__ import annotations

import logging

from app.core.config import get_settings
from app.db.models import Booking, User
from app.modules.notifications.telegram_bot import TelegramBotClient

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self) -> None:
        settings = get_settings()
        self.admin_chat_ids = settings.telegram_admin_chat_ids
        self.bot_client = None
        if settings.telegram_bot_token and settings.telegram_bot_token != "000000:dev-token":
            self.bot_client = TelegramBotClient(settings.telegram_bot_token)

    async def notify_booking_created(self, booking: Booking, user: User) -> None:
        text = (
            f"Новая запись\n"
            f"Услуга: {booking.service_name_snapshot}\n"
            f"Клиент: {booking.client_name}\n"
            f"Телефон: {booking.client_phone}\n"
            f"Старт: {booking.start_at.isoformat()}"
        )
        await self._broadcast(user.telegram_id, text)

    async def notify_booking_cancelled(self, booking: Booking, user: User) -> None:
        text = (
            f"Запись отменена\n"
            f"Услуга: {booking.service_name_snapshot}\n"
            f"Клиент: {booking.client_name}\n"
            f"Старт: {booking.start_at.isoformat()}"
        )
        await self._broadcast(user.telegram_id, text)

    async def notify_status_changed(self, booking: Booking, user: User) -> None:
        text = (
            f"Статус записи изменён\n"
            f"Услуга: {booking.service_name_snapshot}\n"
            f"Статус: {booking.status}\n"
            f"Старт: {booking.start_at.isoformat()}"
        )
        await self._broadcast(user.telegram_id, text)

    async def _broadcast(self, user_chat_id: int, text: str) -> None:
        if not self.bot_client:
            logger.info("Notification skipped because bot token is not configured: %s", text)
            return

        recipients = {user_chat_id, *self.admin_chat_ids}
        for chat_id in recipients:
            try:
                await self.bot_client.send_text(chat_id=chat_id, text=text)
            except Exception:  # pragma: no cover
                logger.exception("Failed to send Telegram notification to chat %s", chat_id)

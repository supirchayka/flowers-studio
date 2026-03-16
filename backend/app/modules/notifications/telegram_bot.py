from __future__ import annotations

from aiogram import Bot


class TelegramBotClient:
    def __init__(self, token: str):
        self.bot = Bot(token=token)

    async def send_text(self, chat_id: int, text: str) -> None:
        await self.bot.send_message(chat_id=chat_id, text=text)


from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.database.models import ProductGroups
from src.database.orm.groups import get_random_group
from src.database.orm.users import get_users
from src.logger import setup_logger


class SpammerService:
    def __init__(self):
        self.logger = setup_logger(__name__)


    async def _create_message(self):
        self.default_message = """🎉 Подпишись на эту группу, чтобы получить бонус! 🎉\n
💠 И получи бонус в виде валюты! 💠"""
        group = await get_random_group()
        self.group_link = group.group_link
        self.default_keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Проверить подписку", callback_data=f"sub_{group.id}")],
            ]
        )

    async def spam(self, bot, user_id):
        users = await get_users()
        count = 0

        for i in users:
            await self._create_message()
            try:
                await bot.send_message(chat_id=i.user_id, text=f"{self.default_message}\n\n<a href='{self.group_link}'>👉Подписаться на группу</a>", reply_markup=self.default_keyboard, parse_mode="HTML")
                count += 1
            except TelegramForbiddenError as te:
                self.logger.warning(te)
                continue
            except Exception as ex:
                self.logger.warning(ex)
                continue

        await bot.send_message(chat_id=user_id,
            text=f"✅ *Рассылка завершена!*\n\n"
             f"📊 *Статистика:*\n"
             f"• Успешно отправлено: {count}\n"
             f"• Всего пользователей: {len(users)}\n",
        parse_mode="Markdown")
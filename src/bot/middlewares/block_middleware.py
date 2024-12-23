from aiogram import BaseMiddleware

from src.database.orm.get_blocks import get_blocks
from src.config.config import settings


class BlockMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        user_id = event.from_user.id
        admin = await get_blocks()
        user_ids = []
        for i in admin:
            user_ids.append(i.user_id)

        # Проверяем, является ли пользователь админом
        if not user_id in user_ids:
            return await handler(event, data)
        else:
            await event.answer("⛔ Вы были заблокированы. Вам запрещено пользоваться ботом!")
            return 

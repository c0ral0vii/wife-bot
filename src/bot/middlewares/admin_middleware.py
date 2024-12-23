from aiogram import BaseMiddleware
from src.database.orm.get_admins import get_admins
from src.config.config import settings

class AdminMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data: dict):
        user_id = event.from_user.id
        admin = await get_admins()
        user_ids = []
        for i in admin:
            user_ids.append(i.user_id)

        # Проверяем, является ли пользователь админом
        if user_id in user_ids or user_id in settings.ADMIN_LIST:
            return await handler(event, data)
        else:
            await event.answer("⛔ Вы не являетесь администратором.")
            return 

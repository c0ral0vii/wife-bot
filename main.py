import asyncio
from aiogram import Bot, Dispatcher, types

from src.logger import setup_logger
from src.config.config import settings
# from src.bot.handlers.admins import (

# )
from src.bot.handlers.chats import (
    shop_handler,
    games_command,
    search_wife,
)
from src.bot.handlers.clients import (
    profiles_handler,
    get_bonus_handler,
    top_users,
    roulete_handler,
)
from src.bot.handlers.commands import (
    start_handler,
)
from src.bot.middlewares import (
    admin_middleware,
    antiflood,
    block_middleware
)

bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher()
logger = setup_logger(__name__)

dp.pre_checkout_query.register(start_handler.on_pre_checkout_query)
dp.message.middleware(antiflood.RateLimitMiddleware())

dp.include_routers(
    shop_handler.router,
    start_handler.router,
    profiles_handler.router,
    get_bonus_handler.router,
    top_users.router,
    roulete_handler.router,
    games_command.router,
    search_wife.router,
)


async def on_starup():
    logger.info("Инициализация")
    commands = [
        types.BotCommand(command="/start", description="Запуск бота"), #
        types.BotCommand(command="/help", description="Помощь"), #
        types.BotCommand(command="/profile", description="Мой профиль"), #
        types.BotCommand(command="/shop", description="Рынок"),  #
        types.BotCommand(command="/bonus", description="Получить ежедневный бонус"), # 
        types.BotCommand(command="/spin", description="Покрутить персонажей"), #
        types.BotCommand(command="/find", description="Найти аниме/мангу"), #
        types.BotCommand(command="/vip", description="Покупка VIP"), #
        types.BotCommand(command="/promo", description="Промокод"), #
        types.BotCommand(command="/trade", description="Обменять"), 
        types.BotCommand(command="/top", description="Топ пользователей"), #
    ]

    await bot.set_my_commands(commands=commands)


async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await on_starup()
    logger.info("Запуск")
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())


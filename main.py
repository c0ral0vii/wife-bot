import asyncio
from aiogram import Bot, Dispatcher, types

from src.logger import setup_logger
from src.bot.handlers.admins import (
    admin_start,

    add_promo,
    add_admins,
    block_users,
    add_group,
    add_vip_user,
)

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
    trade_handler,
    my_wifes,
    select_on_photo,
    everyday_shop,
    main_menu,
    check_group,
)
from src.bot.handlers.commands import (
    start_handler,
)
from src.bot.middlewares import (
    antiflood,
    block_middleware
)
from parser import services


bot = Bot(token="7712843334:AAHaBJKNCYpiDZrGr9K9eeI8oaAkikXaONs")
dp = Dispatcher()
logger = setup_logger(__name__)

dp.pre_checkout_query.register(start_handler.on_pre_checkout_query)


dp.message.middleware(antiflood.RateLimitMiddleware())
dp.message.middleware(block_middleware.BlockMiddleware())
dp.callback_query.middleware(antiflood.RateLimitMiddleware())
dp.callback_query.middleware(block_middleware.BlockMiddleware())


dp.include_routers(
    main_menu.router,
    shop_handler.router,
    my_wifes.router,
    start_handler.router,
    profiles_handler.router,
    get_bonus_handler.router,
    top_users.router,
    roulete_handler.router,
    games_command.router,
    search_wife.router,
    trade_handler.router,
    select_on_photo.router,
    everyday_shop.router,
    check_group.router,

    admin_start.router,
    add_admins.router,
    block_users.router,
    add_promo.router,
    add_group.router,
    add_vip_user.router,
)


async def on_starup():
    logger.info("Инициализация")
    commands = [
        types.BotCommand(command="/start", description="Запуск бота"), #
        types.BotCommand(command="/help", description="Помощь"), #
        types.BotCommand(command="/profile", description="Мой профиль"), #
        types.BotCommand(command="/shop", description="Рынок"),  #
        types.BotCommand(command="/main_menu", description="Главное меню"),  #
        types.BotCommand(command="/everyday_shop", description="Ежедневный магазин"),  #
        types.BotCommand(command="/bonus", description="Получить ежедневный бонус"), # 
        types.BotCommand(command="/spin", description="Покрутить персонажей"), #
        types.BotCommand(command="/find", description="Найти персонажа по имени или айди"), #
        types.BotCommand(command="/find_from_title", description="Найти персонажа по тайтлу"), #
        types.BotCommand(command="/my_wifes", description="Мой гарем"), #
        types.BotCommand(command="/vip", description="Покупка VIP"), #
        types.BotCommand(command="/promo", description="Промокод"), #
        types.BotCommand(command="/games", description="Игры"), #
        types.BotCommand(command="/trade", description="Обменять"), #

        types.BotCommand(command="/trade_shop", description="Рынок обменов"),
        types.BotCommand(command="/top", description="Топ пользователей"), #
    ]

    await bot.set_my_commands(commands=commands)


async def main():
    # await services.parse.parse_page()
    await bot.delete_webhook(drop_pending_updates=True)
    await on_starup()
    logger.info("Запуск")
    await dp.start_polling(bot)


if __name__ == '__main__':
    # asyncio.run(parse.parse_page())
    asyncio.run(main())


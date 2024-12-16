from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


async def start_kb():
    profile = KeyboardButton(text="Профиль")
    bonus = KeyboardButton(text="Получить бонус")
    games = KeyboardButton(text="Игры")
    top_users = KeyboardButton(text="Топ пользователей")
    shop = KeyboardButton(text="Рынок")
    trade = KeyboardButton(text="Обмен")
    find_wife = KeyboardButton(text="Поиск персонажа")
    vip = KeyboardButton(text="Купить VIP")

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [profile, top_users],
            [bonus, games],
            [shop, trade],
            [find_wife, vip],
        ],
        resize_keyboard=True
    )

    return kb
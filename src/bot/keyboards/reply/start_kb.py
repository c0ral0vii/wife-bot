from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


async def start_kb():
    profile = KeyboardButton(text="🎡 Крутить персонажа")
    main_menu = KeyboardButton(text="🏠 Главное меню")
    bonus = KeyboardButton(text="🎁 Получить бонус")
    trade = KeyboardButton(text="🔄 Обмен")
    find_wife = KeyboardButton(text="🔍 Поиск персонажа")

    kb = ReplyKeyboardMarkup(
        keyboard=[
            [main_menu],
            [profile, bonus],
            [trade, find_wife],
        ],
        resize_keyboard=True
    )

    return kb
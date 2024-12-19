from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.logger import setup_logger
from src.database.orm.roulete import spin_character
from src.database.orm.users import remove_balance
from decimal import Decimal
import os
import asyncio


router = Router()
logger = setup_logger(__name__)


@router.message(F.text == "Крутить персонажа")
@router.message(F.text == "!крутить")
@router.message(Command("spin"))
async def roulte_characters(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="- случайный персонаж: 💠 250", callback_data="random_spin")],
            [InlineKeyboardButton(text="- персонаж с выбранного тайтла: 💠 500", callback_data="select_spin")],

        ]
    )
    await message.answer(f"🎟{message.from_user.username}, выберите желаемую опцию::", reply_markup=kb)


@router.callback_query(F.data == "random_spin")
async def random_spin_handler(callback: types.CallbackQuery, bot: Bot):
    try:
        # Прокрутка случайного персонажа
        balance = await remove_balance(user_id=callback.from_user.id, amount_to_remove=Decimal(250))
        if balance is False:
            await callback.message.answer("Недостаточно средств на балансе")
            return

        result = await spin_character(user_id=callback.from_user.id)
        user_photo_path = f"./media/wifes/{result.id}/profile.png"
        default_photo_path = "./media/wifes/default.png"

        if os.path.exists(user_photo_path) and os.path.isfile(user_photo_path):
            photo = types.FSInputFile(path=user_photo_path)
        else:
            photo = types.FSInputFile(path=default_photo_path)

        await callback.message.answer_photo(photo=photo, caption=f"""Вы получили персонажа:
                                    \n🆔{result.id} 
                                   \n👤Полное имя: {result.name}
                                   \n🌸 Тайтл: {result.from_}
                                   \n💎Редкость: {result.rare.value}
                                   """)
    except ValueError as e:
        await callback.message.answer(str(e))
    await callback.answer()

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.logger import setup_logger
from src.database.orm.users import get_top_users_by_characters, get_top_users_by_legendary


router = Router()
logger = setup_logger(__name__)


@router.message(F.text == "!топ")
@router.message(F.text == "Топ пользователей")
@router.message(Command("top"))
async def top_users(message: types.Message):
    top_users = await get_top_users_by_characters(limit=10)
    
    top_kb = [
        [InlineKeyboardButton(text='Топ по легендаркам', callback_data='top_legendary')],
    ]
    top = 1
    for user in top_users:
        top_kb.append([InlineKeyboardButton(text=f"{top}. {user.username}-{user.characters_count}", callback_data=f"detail")])
        top += 1

    kb = InlineKeyboardMarkup(
            inline_keyboard=top_kb
        )
    
    await message.answer(text=f"Топ пользователей по персонажам:", reply_markup=kb)


@router.callback_query(F.data == "top_legendary")
async def top_legendary(callback: types.CallbackQuery):
    top_users = await get_top_users_by_legendary(limit=10)
    await callback.message.delete()
    top_kb = [
    ]
    top = 1
    for user in top_users:
        top_kb.append([InlineKeyboardButton(text=f"{top}. {user.username}", callback_data=f"detail")])
        top += 1

    kb = InlineKeyboardMarkup(
            inline_keyboard=top_kb
        )
    
    await callback.message.answer(text=f"Топ пользователей по легендаркам:", reply_markup=kb)
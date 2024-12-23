from aiogram import Router, F, types
from aiogram.filters import StateFilter, Command
from src.bot.middlewares import admin_middleware
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


router = Router()
router.message.middleware(admin_middleware.AdminMiddleware())


@router.message(Command("admin"))
async def start_admin(message: types.Message):
    await message.answer("Вы вошли в админ панель", 
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                                 [InlineKeyboardButton(text="Заблокировать пользователя", callback_data="banned_user"), InlineKeyboardButton(text="Админы", callback_data=f"added_admin")],
                                 [InlineKeyboardButton(text="Добавить рекламу", callback_data="promoute"), InlineKeyboardButton(text="Добавить промокод", callback_data="promocode")]
                             ]
                         ))
    

@router.callback_query(F.data == "banned_user")
async def banned_user(callback: types.CallbackQuery):
    ...


@router.callback_query(F.data == "added_admin")
async def admins(callback: types.CallbackQuery):
    ...


@router.callback_query(F.data == "promoute")
async def promoute(callback: types.CallbackQuery):
    ...


@router.callback_query(F.data == "promocode")
async def promo(callback: types.CallbackQuery):
    ...
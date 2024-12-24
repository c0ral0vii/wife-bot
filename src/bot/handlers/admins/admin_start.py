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
                                 [InlineKeyboardButton(text="Заблокировать пользователя 🚫",
                                                       callback_data="banned_user"),
                                  InlineKeyboardButton(text="Админы 👑", callback_data="added_admin")],
                                 [InlineKeyboardButton(text="Добавить рекламу 📢", callback_data="promoute"),
                                  InlineKeyboardButton(text="Добавить промокод 🎟️", callback_data="promocode")]
                             ]
                         ))


@router.callback_query(F.data == "banned_user")
async def banned_user(callback: types.CallbackQuery):
    await callback.message.answer("Действия с заблокированными:", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Разблокировать пользователя ✅", callback_data="unblock_user"),
             InlineKeyboardButton(text="Заблокировать пользователя 🚫", callback_data="block_user")],
            [InlineKeyboardButton(text="Список заблокированных 📜", callback_data="list_block")],
        ]
    ))


@router.callback_query(F.data == "added_admin")
async def admins(callback: types.CallbackQuery):
    await callback.message.answer("Действия с админами:", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить админа 👑", callback_data="add_admin"),
             InlineKeyboardButton(text="Удалить админа ❌", callback_data="remove_admin")],
            [InlineKeyboardButton(text="Список админов 📋", callback_data="list_admin")],
        ]
    ))


@router.callback_query(F.data == "promoute")
async def promoute(callback: types.CallbackQuery):
    await callback.message.answer("Действия с рекламой:", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить группу для рекламы 📢", callback_data="add_group"),
             InlineKeyboardButton(text="Удалить группу ❌", callback_data="remove_group")],
            [InlineKeyboardButton(text="Список рекламных групп 📜", callback_data="list_group")],
        ]
    ))


@router.callback_query(F.data == "promocode")
async def promo(callback: types.CallbackQuery):
    await callback.message.answer("Действия с промокодами:", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Добавить промокод 🎟️", callback_data="add_promo"),
             InlineKeyboardButton(text="Удалить промокод ❌", callback_data="remove_promo")],
            [InlineKeyboardButton(text="Список промокодов 📋", callback_data="list_promo")],
        ]
    ))
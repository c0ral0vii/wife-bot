from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.handlers import MessageHandler
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.bot.middlewares.admin_middleware import AdminMiddleware
from src.database.orm.get_admins import add_admin, remove_admin, get_admins

router = Router()
router.message.middleware(AdminMiddleware())

class AddAdmin(StatesGroup):
    add = State()
    delete = State()


@router.callback_query(F.data == "add_admin")
async def add_admins(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddAdmin.add)
    await callback.message.answer("Отправьте юзер айди нового админа")


@router.message(F.text, StateFilter(AddAdmin.add))
async def add(message: types.Message, state: FSMContext):
    result = await add_admin(user_id=message.text)
    await message.answer(result["message"])
    await state.clear()


@router.callback_query(F.data == "remove_admin")
async def delete_admin(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddAdmin.delete)
    await callback.message.answer("Отправьте юзер айди которого нужно удалить")


@router.message(F.text, StateFilter(AddAdmin.delete))
async def delete(message: types.Message, state: FSMContext):
    result = await remove_admin(user_id=message.text)
    await message.answer(result["message"])
    await state.clear()


@router.callback_query(F.data == "list_admin")
async def get_list_admin(callback: types.CallbackQuery, state: FSMContext):
    message_text = "Все админы:"
    admins = await get_admins()


    # Создаем клавиатуру с кнопками для каждого админа
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{admin.user_id}", callback_data=f"nothing")]
            for admin in admins
        ]
    )

    # Отправляем сообщение с клавиатурой
    await callback.message.answer(message_text, reply_markup=keyboard)

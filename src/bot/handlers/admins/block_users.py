from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from src.bot.middlewares.admin_middleware import AdminMiddleware
from src.database.orm.get_blocks import get_blocks, add_block, remove_block


router = Router()
router.message.middleware(AdminMiddleware())


class AddBlockUser(StatesGroup):
    add = State()
    delete = State()


@router.callback_query(F.data == "block_user")
async def add_block_user(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddBlockUser.add)
    await callback.message.answer("Отправьте юзер айди пользователя которого нужно заблокировать")


@router.message(F.text, StateFilter(AddBlockUser.add))
async def add(message: types.Message, state: FSMContext):
    result = await add_block(user_id=message.text)
    await message.answer(result["message"])
    await state.clear()


@router.callback_query(F.data == "unblock_user")
async def delete_admin(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddBlockUser.delete)
    await callback.message.answer("Отправьте юзер айди пользователя которого нужно разблокировать")


@router.message(F.text, StateFilter(AddBlockUser.delete))
async def delete(message: types.Message, state: FSMContext):
    result = await remove_block(user_id=message.text)
    await message.answer(result["message"])
    await state.clear()


@router.callback_query(F.data == "list_block")
async def get_list_admin(callback: types.CallbackQuery, state: FSMContext):
    message_text = "Все заблокированные:"
    admins = await get_blocks()


    # Создаем клавиатуру с кнопками для каждого админа
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{admin.user_id}", callback_data=f"nothing")]
            for admin in admins
        ]
    )

    # Отправляем сообщение с клавиатурой
    await callback.message.answer(message_text, reply_markup=keyboard)

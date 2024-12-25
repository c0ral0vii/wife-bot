from aiogram import Router, F, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from src.bot.middlewares.admin_middleware import AdminMiddleware
from src.database.orm.promo import get_promo, add_promo, delete_promo

router = Router()
router.message.middleware(AdminMiddleware())


class AddPromo(StatesGroup):
    add = State()
    remove = State()


@router.callback_query(F.data == "add_promo")
async def add_promo_callback_query(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите новый промокод и через пробел сколько он будет давать бонусов(ПРОМОКОД 1000):")
    await state.set_state(AddPromo.add)


@router.message(F.text, StateFilter(AddPromo.add))
async def message_add_promo(message: types.Message, state: FSMContext):
    data = message.text.split(" ")
    if len(data) > 2 and len(data) < 2:
        await message.answer("Неверный формат, попробуйте снова")
        return

    promo = data[0]
    promo_bonus = data[-1]

    result = await add_promo(promocode=promo, bonus=int(promo_bonus))

    await message.answer(result["message"])
    await state.clear()


@router.callback_query(F.data == "remove_promo")
async def remove_promo_callback_query(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите промокод для удаления")
    await state.set_state(AddPromo.remove)


@router.message(F.text, StateFilter(AddPromo.add))
async def message_add_promo(message: types.Message, state: FSMContext):
    data = message.text.split(" ")

    promo = data[0]


    result = await delete_promo(promocode=promo)

    await message.answer(result["message"])
    await state.clear()


@router.callback_query(F.data == "add_promo")
async def list_promo_callback_query(callback: CallbackQuery, state: FSMContext):
    promos = await get_promo(admin=True)
    message_text = "Все заблокированные:"

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{promo.promo}-{promo.bonus}", callback_data=f"nothing")]
            for promo in promos
        ]
    )

    await callback.message.answer(message_text, reply_markup=keyboard)
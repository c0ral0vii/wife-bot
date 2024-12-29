from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton



router = Router()

class Use_MainMenu(StatesGroup):
    user = State()


@router.message(F.text == "🏠 Главное меню")
@router.message(Command("main_menu"))
async def main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(Use_MainMenu.user)
    await state.update_data(user=message.from_user.id)

    await message.answer("🏠 Главное меню",
                         reply_markup=InlineKeyboardMarkup(
                             inline_keyboard=[
                                [InlineKeyboardButton(text="👤 Профиль", callback_data="profile"), InlineKeyboardButton(text="🛒 Рынок", callback_data="shop")],
                                [InlineKeyboardButton(text="🎮 Мини-игры", callback_data="mini-games")],
                                [InlineKeyboardButton(text="👫 Мой гарем", callback_data="my_wifes"), InlineKeyboardButton(text="📞 Обратная связь", callback_data="feedback")],
                                [InlineKeyboardButton(text="💎 Купить VIP", callback_data="buy_vip")],
                            ]))


@router.callback_query(F.data == "feedback")
async def feedback(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Для обратной связи отпишите нам - @Sm0keLuv")
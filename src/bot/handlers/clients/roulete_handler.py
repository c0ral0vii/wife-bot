from aiogram import Router, F, types, Bot
from aiogram.filters import Command, StateFilter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.logger import setup_logger
from src.database.orm.roulete import spin_character
from src.database.orm.users import remove_balance
from decimal import Decimal
import os
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from src.database.orm.find import find_characters
from src.database.orm.users import get_user

router = Router()
logger = setup_logger(__name__)

@router.callback_query(F.data == "spins")
async def call_spin(callback: types.CallbackQuery):
    await roulte_characters(message=callback.message)


@router.message(F.text == "🎡 Крутить персонажа")
@router.message(Command("spin"))
async def mess_spin(message: types.Message):
    await roulte_characters(message=message)


async def roulte_characters(message: types.Message):
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Случайный персонаж: 💠 250", callback_data="random_spin")],
            [InlineKeyboardButton(text="Персонаж с выбранного тайтла: 💠 500", callback_data="select_spin")],

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
        user = await get_user(user_id=callback.from_user.id)
        user_photo_path = f"./media/wifes/{result.id}/profile.png"
        default_photo_path = "./media/wifes/default.png"

        if os.path.exists(user_photo_path) and os.path.isfile(user_photo_path):
            photo = types.FSInputFile(path=user_photo_path)
        else:
            photo = types.FSInputFile(path=default_photo_path)
        wife_rare = result.rare.value
        if wife_rare == "Легендарный":
            color = "🟠"
        elif wife_rare == "Редкий":
            color = "🟢"
        elif wife_rare == "Обычный":
            color = "⚪️"
        else:
            color = "🟣" 
        await callback.message.answer_photo(photo=photo, caption=f"""{callback.from_user.username}, вам выпал: \n🆔 {result.id} \n👤 Полное имя: {result.name} \n🌸 Тайтл: {result.from_.split(",")[0]} \n💎 Редкость: {color}{result.rare.value}\n\nОсталось 💠{user.balance}""", reply_markup=InlineKeyboardMarkup(
                                       inline_keyboard=[
                                           [InlineKeyboardButton(text="👤Установить на аву", callback_data=f"set_on_photo_{result.id}")],
                                           [InlineKeyboardButton(text="🔄Крутить снова", callback_data="random_spin")]
                                       ]
                                   ))
    except ValueError as e:
        await callback.message.answer(str(e), reply_markup=InlineKeyboardMarkup(
                                       inline_keyboard=[
                                           [InlineKeyboardButton(text="🔄Крутить снова", callback_data="random_spin")]
                                       ]
                                   ))


class TitleState(StatesGroup):
    title = State()


@router.callback_query(F.data == "select_spin")
async def select_spin(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(TitleState.title)
    await state.update_data(use_user_id=callback.from_user.id)
    await callback.message.answer("Укажите тайтл по которому вы хотите крутить:")


@router.message(F.text, StateFilter(TitleState))
async def title_spin(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if int(message.from_user.id) != int(data["use_user_id"]):
        return
    
    title = message.text
    
    result = await find_characters(text=title, from_title=True)
    if not result:
        await message.answer("По данному тайтлу не найдены персонажи")
        return
    try:
        # Прокрутка случайного персонажа
        balance = await remove_balance(user_id=message.from_user.id, amount_to_remove=Decimal(250))
        if balance is False:
            await message.answer("Недостаточно средств на балансе")
            return

        result = await spin_character(user_id=message.from_user.id, characters=result)
        user = await get_user(user_id=message.from_user.id)
        user_photo_path = f"./media/wifes/{result.id}/profile.png"
        default_photo_path = "./media/wifes/default.png"

        if os.path.exists(user_photo_path) and os.path.isfile(user_photo_path):
            photo = types.FSInputFile(path=user_photo_path)
        else:
            photo = types.FSInputFile(path=default_photo_path)
        wife_rare = result.rare.value
        if wife_rare == "Легендарный":
            color = "🟠"
        elif wife_rare == "Редкий":
            color = "🟢"
        elif wife_rare == "Обычный":
            color = "⚪️"
        else:
            color = "🟣" 

        await message.answer_photo(photo=photo, caption=f"{message.from_user.username}, вам выпал {color}{result.name} ({result.from_.split(",")[0]}) он отправляется в ваш горем\n\nОсталось 💠{user.balance}", reply_markup=InlineKeyboardMarkup(
                                       inline_keyboard=[
                                           [InlineKeyboardButton(text="👤Установить на аву", callback_data=f"set_on_photo_{result.id}")],
                                           [InlineKeyboardButton(text="🔄Крутить снова", callback_data="select_spin")]
                                       ]
                                   ))
    except ValueError as e:
        await message.answer(str(e), reply_markup=InlineKeyboardMarkup(
                                       inline_keyboard=[
                                           [InlineKeyboardButton(text="🔄Крутить снова", callback_data="select_spin")]
                                       ]
                                   ))
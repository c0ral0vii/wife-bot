from aiogram import Router, F, types
from aiogram.filters import Command
from src.logger import setup_logger
from src.database.orm.find import find_characters
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.database.orm.wifes import get_character
import os


router = Router()
logger = setup_logger(__name__)

class FindState(StatesGroup):
    find = State()
    title = State()

@router.message(F.text.startswith("🔍 Поиск персонажа"))
@router.message(Command("find"))
async def find_character(message: types.Message, state: FSMContext):
    await state.set_state(FindState.find)
    await state.update_data(use_user_id=message.from_user.id)

    await message.answer("Введите имя или айди персонажа")


@router.message(StateFilter(FindState.find))
async def find(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if int(message.from_user.id) != int(data["use_user_id"]):
        return
    text = message.text.lower()

    result = await find_characters(text=text)

    if not result:
        await message.answer("Не найдено")
        await state.clear()
    else:
        message_text = ""
        kb = []
        for i in result:
            message_text += f"\n {i.name} | ID: {i.id}"
            kb.append(InlineKeyboardButton(text=f"ID: {i.id}", callback_data=f"select_{i.id}"))

        await message.answer(text=message_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[kb]))
        await state.clear()


@router.message(Command("find_from_title"))
async def find_character_title(message: types.Message, state: FSMContext):
    await state.set_state(FindState.title)
    await state.update_data(use_user_id=message.from_user.id)

    await message.answer("Введите тайтл персонажа")


@router.message(StateFilter(FindState.title))
async def find_character_from_title(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if int(message.from_user.id) != int(data["use_user_id"]):
        return
    text = message.text.lower()

    result = await find_characters(text=text, from_title=True)
    if not result:
        await message.answer("Не найдено")
        await state.clear()
    else:
        message_text = ""
        kb = []
        for i in result:
            message_text += f"\n {i.name} | ID: {i.id}"
            kb.append(InlineKeyboardButton(text=f"ID: {i.id}", callback_data=f"select_{i.id}"))

        await message.answer(text=message_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[kb]))


@router.callback_query(F.data.startswith("select_"))
async def select_wife(callback: types.CallbackQuery, state: FSMContext):
    callback_data = callback.data.split("_")[-1]
    
    character = await get_character(id=int(callback_data))
    user_photo_path = f"./media/wifes/{character.id}/profile.png"
    default_photo_path = "./media/wifes/default.png"

    if os.path.exists(user_photo_path) and os.path.isfile(user_photo_path):
        photo = types.FSInputFile(path=user_photo_path)
    else:
        photo = types.FSInputFile(path=default_photo_path)

    await callback.message.answer_photo(photo=photo, caption=f"""Информация о персонаже:
                                \n🆔{character.id} 
                                \n👤Полное имя: {character.name}
                                \n🌸 Тайтл: {character.from_[:120]}
                                \n💎Редкость: {character.rare.value}
                                """)
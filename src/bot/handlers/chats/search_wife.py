from aiogram import Router, F, types
from aiogram.filters import Command
from src.logger import setup_logger
from src.database.orm.find import find_characters
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import os

router = Router()
logger = setup_logger(__name__)

class FindState(StatesGroup):
    find = State()


@router.message(Command("find"))
async def find_character(message: types.Message, state: FSMContext):
    await state.set_state(FindState.find)
    await state.update_data(use_user_id=message.from_user.id)

    await message.answer("Введите имя или мангу/аниме/игру откуда он может быть")


@router.message(StateFilter(FindState.find))
async def find(message: types.Message, state: FSMContext):
    data = await state.get_data()
    if int(message.from_user.id) != int(data["use_user_id"]):
        return
    text = message.text.lower()

    result = await find_characters(text=text)

    if not result:
        await message.answer("Не найдено")
    else:
        user_photo_path = f"./media/wifes/{result.id}/profile.png"
        default_photo_path = "./media/wifes/default/default.png"

        if os.path.exists(user_photo_path) and os.path.isfile(user_photo_path):
            photo = types.FSInputFile(path=user_photo_path)
        else:
            photo = types.FSInputFile(path=default_photo_path)

        await message.answer_photo(photo=photo, caption=f"Найден персонаж: {result.name} ({result.rare.value})")
        await state.clear()


from aiogram import Router, F, types, Bot
from aiogram.filters import Command, StateFilter
from src.database.orm.wifes import my_wifes
from src.logger import setup_logger
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from more_itertools import chunked
from src.database.orm.wifes import get_character
from src.bot.keyboards.inline.pagination_kb import pagination_kb
import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


router = Router()
logger = setup_logger(__name__)


class PaginationState(StatesGroup):
    page = State()

    max_pages = State()
    pages = State()
    use_user_id = State()


@router.callback_query(F.data == "my_wifes")
async def call_my_wifes(callback: types.CallbackQuery, state: FSMContext):
    await all_my_wifes(callback=callback, state=state)

@router.message(Command("my_wifes"))
async def mess_my_wifes(message: types.Message, state: FSMContext):
    await all_my_wifes(callback=message, state=state, message=True)

async def all_my_wifes(callback: types.CallbackQuery | types.Message, state: FSMContext, message=False):
    await state.clear()
    user_id = callback.from_user.id
    wifes = await my_wifes(user_id=user_id)
    chunks = list(chunked(wifes, 5))
    await state.set_state(PaginationState.page)
    await state.update_data(page=1, max_pages=len(chunks), pages=chunks, use_user_id=user_id)

    if message:
        if len(chunks) > 0:
            await callback.answer("Ваш гарем:", reply_markup=await pagination_kb(page=1, list_requests=chunks[0], max_page=len(chunks), user_id=user_id, my_slots=True))
        else:
            await callback.answer("Ваш гарем пуст")
    if len(chunks) > 0:
        await callback.message.answer("Ваш гарем:", reply_markup=await pagination_kb(page=1, list_requests=chunks[0], max_page=len(chunks), user_id=user_id, my_slots=True))
    else:
        await callback.message.answer("Ваш гарем пуст")


@router.callback_query(F.data.startswith("refresh_"), StateFilter(PaginationState))
async def shop_refresh(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    callback_data = callback.from_user.id

    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    user_id = callback.from_user.id
    page = data["page"]
    wifes = await my_wifes(user_id=user_id)

    chunks = list(chunked(wifes, 5))

    await state.update_data(page=page, max_pages=len(chunks), pages=chunks)
    await callback.message.delete()
    await callback.message.answer(text="Ваш гарем:", reply_markup=await pagination_kb(page=page, max_page=len(chunks),
                                                                                          list_requests=chunks[page - 1], user_id=callback_data))


@router.callback_query(lambda query: "right_pagination_" in query.data, StateFilter(PaginationState))
async def to_right(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()

    callback_data = callback.from_user.id

    
    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    logger.debug(data)

    page = data['page']
    pages = data['pages']
    max_pages = data['max_pages']

    if max_pages <= page:
        logger.debug(max_pages)
        return

    page += 1
    await state.update_data(page=page)
    await callback.message.edit_text(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=max_pages, list_requests=pages[page-1]))


@router.callback_query(lambda query: "left_pagination_" in query.data, StateFilter(PaginationState))
async def to_left(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    callback_data = callback.from_user.id
    
    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    logger.debug(data)
    page = data['page']
    pages = data['pages']
    max_pages = data['max_pages']

    if 1 == page:
        return

    page -= 1
    await state.update_data(page=page)
    await callback.message.edit_text(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=max_pages, list_requests=pages[page-1]))


@router.callback_query(lambda query: "select_" in query.data, StateFilter(PaginationState))
async def select_wife(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    callback_data = callback.from_user.id

    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    callback_data = callback.data.split("_")[-1]
    
    character = await get_character(id=int(callback_data))
    user_photo_path = f"./media/wifes/{character.id}/profile.png"
    default_photo_path = "./media/wifes/default.png"

    if os.path.exists(user_photo_path) and os.path.isfile(user_photo_path):
        photo = types.FSInputFile(path=user_photo_path)
    else:
        photo = types.FSInputFile(path=default_photo_path)
    wife_rare = character.rare.value
    if wife_rare == "Легендарный":
        color = "🟠"
    elif wife_rare == "Редкий":
        color = "🟢"
    elif wife_rare == "Обычный":
        color = "⚪️"
    else:
        color = "🟣" 
    await callback.message.answer_photo(photo=photo, caption=f"""Информация о персонаже:\n🆔 {character.id}\n👤 Полное имя: {character.name}\n🌸 Тайтл: {character.from_.split(",")[0]}\n💎 Редкость: {color}{character.rare.value}
                                """, reply_markup=InlineKeyboardMarkup(
                                    inline_keyboard=[
                                        [InlineKeyboardButton(text="Установить на аву", callback_data=f"set_on_photo_{character.id}")]
                                    ]
                                ))
from aiogram import Router, F, types, Bot
from aiogram.filters import StateFilter, Command
from src.database.orm.trade import answer_trade
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.logger import setup_logger
from src.bot.keyboards.inline.pagination_kb import pagination_kb
from src.database.orm.shops import get_wifes_for_user
from more_itertools import chunked


router = Router()
logger = setup_logger(__name__)


class TradeState(StatesGroup):
    use_user_id = State()
    to_user_id = State()

    page = State()
    max_page = State()
    pages = State()


@router.message(Command("trade"))
@router.message(F.text.startswith("Обмен"))
async def trade(message: types.Message, bot: Bot, state: FSMContext):
    text = message.text.split(" ")

    if len(text) != 2:
        await message.answer("Не правильный формат\n\nВот так выглядит обмен - /trade <user_id>")
    
    user_id = message.from_user.id
    characters = await get_wifes_for_user(user_id=user_id)
    chunks = list(chunked(characters, 5))
    await state.update_data(page=1, max_pages=len(chunks), pages=chunks, use_user_id=user_id, to_=text[-1].strip())

    await state.set_state(TradeState.use_user_id)

    await message.answer("Учтите получить одинаковых персонажей дважды нельзя\n\nВаши персонажи для обмена:", reply_markup=await pagination_kb(page=1, list_slots=chunks[0], max_page=len(chunks), user_id=user_id, my_slots=True, trade=True))
    

@router.callback_query(F.data.startswith("trade_refresh_"))
async def shop_refresh(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    callback_data = callback.data.split("_")[-1]

    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    chat_id = callback.message.chat.id
    page = data["page"]
    slots = await get_wifes_for_user(chat_id=chat_id)

    chunks = list(chunked(slots, 5))

    await state.update_data(page=page, max_pages=len(chunks), pages=chunks)
    await callback.message.delete()
    await callback.message.answer(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=len(chunks),
                                                                                          list_slots=chunks[page - 1], user_id=callback_data))

@router.callback_query(lambda query: "trade_right_pagination_" in query.data)
async def to_right(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()

    callback_data = callback.data.split("_")[-1]
    
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
    await callback.message.edit_text(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=max_pages, list_slots=pages[page-1]))


@router.callback_query(lambda query: "trade_left_pagination_" in query.data)
async def to_left(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    callback_data = callback.data.split("_")[-1]
    
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
    await callback.message.edit_text(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=max_pages, list_slots=pages[page-1]))


@router.callback_query(F.data.startswith("trade_"))
async def to_trade(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    callback_data = callback.data.split("_")[-1]
    
    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    
    await callback.message.answer("Ваш запрос отправлен")
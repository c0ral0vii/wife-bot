from aiogram import Router, F, types, Bot
from aiogram.filters import StateFilter, Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.logger import setup_logger
from src.bot.keyboards.inline.pagination_kb import pagination_kb
from src.database.orm.shops import get_wifes_for_user
from more_itertools import chunked
from src.database.orm.users import get_user
from src.database.orm.trade import send_trade, cancel_trade, accept_trade_with_exchange, final_accept_trade_with_exchange
from src.database.orm.wifes import get_character


router = Router()
logger = setup_logger(__name__)


class TradeState(StatesGroup):
    use_user_id = State()
    to_user_id = State()

    page = State()
    max_page = State()
    pages = State()


def contains_only_digits(text: str) -> bool:
    return text.isdigit()


@router.message(F.text.startswith("🔄 Обмен"))
async def trade_shop(message: types.Message, state: FSMContext):
    await message.answer("🔄 *Рынок обменов*", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Все обмены", callback_data="shop_trades")],
            [InlineKeyboardButton(text="➕ Создать обмен", callback_data="create_trade")],
            [InlineKeyboardButton(text="👤 Ваши обмены", callback_data="my_trades")],
        ]
    ),
    parse_mode="Markdown")


@router.callback_query(F.data.startswith("my_trades"))
async def trade_shop(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("🔄 *Ваши обменs*", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать обмен", callback_data="create_trade")],
        ]
    ),
    parse_mode="Markdown")


@router.message(Command("trade"))
async def trade(message: types.Message, bot: Bot, state: FSMContext):
    text = message.text.split(" ")

    if len(text) != 2 or not contains_only_digits(text[-1]):
        await message.answer("Не правильный формат\n\nВот так выглядит обмен - /trade <user_id>")
        return
    
    user_id=int(text[-1].strip())
    to_user = await get_user(user_id=user_id)
    if not to_user:
        await message.answer("Такого пользователя нет")
        return
    if user_id == message.from_user.id:
        await message.answer("Вы не можете отправлять обмен самому себе")
        return
    
    user_id = message.from_user.id
    characters = await get_wifes_for_user(user_id=user_id)
    chunks = list(chunked(characters, 5))
    await state.update_data(page=1, max_pages=len(chunks), pages=chunks, use_user_id=user_id, to_=to_user)

    await state.set_state(TradeState.use_user_id)

    await message.answer("Учтите получить одинаковых персонажей дважды нельзя\n\nВаши персонажи для обмена:", reply_markup=await pagination_kb(page=1, list_requests=chunks[0], max_page=len(chunks), user_id=user_id, my_slots=True, trade=True))
    

@router.callback_query(F.data.startswith("trade_refresh_"), StateFilter(TradeState))
async def shop_refresh(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    callback_data = callback.from_user.id

    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    page = data["page"]
    slots = await get_wifes_for_user(user_id=callback_data)

    chunks = list(chunked(slots, 5))

    await state.update_data(page=page, max_pages=len(chunks), pages=chunks)
    await callback.message.delete()
    await callback.message.answer(text="Учтите получить одинаковых персонажей дважды нельзя\n\nВаши персонажи для обмена:", reply_markup=await pagination_kb(page=page, max_page=len(chunks),
                                                                                          list_requests=chunks[page - 1], user_id=callback_data, trade=True))


@router.callback_query(lambda query: "trade_right_pagination_" in query.data, StateFilter(TradeState))
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
    await callback.message.edit_text(text="Учтите получить одинаковых персонажей дважды нельзя\n\nВаши персонажи для обмена:", reply_markup=await pagination_kb(page=page, max_page=max_pages, list_requests=pages[page-1], trade=True))


@router.callback_query(lambda query: "trade_left_pagination_" in query.data, StateFilter(TradeState))
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
    await callback.message.edit_text(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=max_pages, list_requests=pages[page-1], trade=True))


@router.callback_query(F.data.startswith("trade_"), StateFilter(TradeState))
async def to_trade(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    callback_data = callback.from_user.id
    
    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    
    wife_id = callback.data.split("_")[-1]
    to_ = data["to_"]
    character = await get_character(id=int(wife_id))
    trade = await send_trade(
        from_user_id=callback.from_user.id,
        to_user_id=int(to_.user_id),
        wife_id=int(wife_id),
    )
    await bot.send_message(chat_id=to_.user_id ,text="👀Вам пришел запрос на обмен:", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Его вайфа: ID: {character.id}, {character.name}, ({character.rare.value})", callback_data=f"test")],
            [InlineKeyboardButton(text="✅", callback_data=f"accept_trade_{trade.id}"),
            InlineKeyboardButton(text="❌", callback_data=f"close_trade_{trade.id}"),]
        ]
    ))

    await callback.message.answer("✅Ваш запрос на обмен отправлен")

class AcceptTrade(StatesGroup):
    accept_trade = State()

@router.callback_query(F.data.startswith("accept_trade_"))
async def accept_trade(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AcceptTrade.accept_trade)
    user_id = callback.from_user.id
    characters = await get_wifes_for_user(user_id=user_id)
    chunks = list(chunked(characters, 5))

    await state.update_data(page=1, max_pages=len(chunks), pages=chunks, use_user_id=user_id, trade_id=int(callback.data.split("_")[-1]))

    await callback.message.answer("Выберите вайфу для обмена.\n\nПосле выбора вы автоматически примете обмен с вашей стороны:", reply_markup=await pagination_kb(page=1, list_requests=chunks[0], max_page=len(chunks), user_id=user_id, my_slots=True, trade=True))


@router.callback_query(F.data.startswith("trade_refresh_"), StateFilter(AcceptTrade))
async def shop_refresh(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    callback_data = callback.from_user.id

    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    
    page = data["page"]
    slots = await get_wifes_for_user(user_id=callback_data)

    chunks = list(chunked(slots, 5))

    await state.update_data(page=page, max_pages=len(chunks), pages=chunks)
    await callback.message.delete()
    await callback.message.answer(text="Учтите получить одинаковых персонажей дважды нельзя\n\nВаши персонажи для обмена:", reply_markup=await pagination_kb(page=page, max_page=len(chunks),
                                                                                          list_requests=chunks[page - 1], user_id=callback_data, trade=True))


@router.callback_query(lambda query: "trade_right_pagination_" in query.data, StateFilter(AcceptTrade))
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
    await callback.message.edit_text(text="Учтите получить одинаковых персонажей дважды нельзя\n\nВаши персонажи для обмена:", reply_markup=await pagination_kb(page=page, max_page=max_pages, list_requests=pages[page-1], trade=True))


@router.callback_query(lambda query: "trade_left_pagination_" in query.data, StateFilter(AcceptTrade))
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
    await callback.message.edit_text(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=max_pages, list_requests=pages[page-1], trade=True))


@router.callback_query(F.data.startswith("trade_"), StateFilter(AcceptTrade))
async def to_trade(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    callback_data = callback.from_user.id
    
    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    
    wife_id = callback.data.split("_")[-1]

    trade = await accept_trade_with_exchange(
        trade_id=int(data["trade_id"]),
        exchange_wife_id=int(wife_id),
    )
    first_wife = await get_character(id=int(wife_id))
    second_wife = await get_character(id=trade.change_from_id)
    print(trade.from_.user_id)
    await bot.send_message(chat_id=int(trade.from_.user_id),text="👀Примите окончательное решение:", reply_markup=InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Его вайфа: {first_wife.name} ({first_wife.rare.value})", callback_data=f"test")],
            [InlineKeyboardButton(text=f"Ваша вайфа: {second_wife.name} ({second_wife.rare.value})", callback_data=f"test")],
            [InlineKeyboardButton(text="✅", callback_data=f"final_accept_trade_{trade.id}"),
            InlineKeyboardButton(text="❌", callback_data=f"final_close_trade_{trade.id}"),]
        ]
    ))

    await callback.message.answer("✅Ожидаем окончательного принятия обмена")

@router.callback_query(F.data.startswith("final_accept_trade_"))
async def final_accept_trade(callback: types.CallbackQuery, bot: Bot):
    callback_data = callback.data.split("_")[-1]
    await callback.message.delete()
    try:
        trade = await final_accept_trade_with_exchange(trade_id=int(callback_data))
        await bot.send_message(chat_id=trade.from_.user_id, text="❌Обмен отменен")
        await bot.send_message(chat_id=trade.to_.user_id, text="❌Обмен отменен")
    except ValueError:
        await callback.message.answer("Эти вайфы у вас уже есть")
        return
    await bot.send_message(chat_id=trade.to_.user_id, text="✅Трейд подтвержден")
    await bot.send_message(chat_id=trade.from_.user_id, text="✅Трейд подтвержден")


@router.callback_query(F.data.startswith("close_trade_"))
@router.callback_query(F.data.startswith("final_close_trade_"))
async def close_trade(callback: types.CallbackQuery, bot: Bot):
    trade = await cancel_trade(trade_id=int(callback.data.split("_")[-1]))
    await callback.message.delete()
    await bot.send_message(chat_id=trade.from_.user_id, text="❌Обмен отменен")
    await bot.send_message(chat_id=trade.to_.user_id, text="❌Обмен отменен")


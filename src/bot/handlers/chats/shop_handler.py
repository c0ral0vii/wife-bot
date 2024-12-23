from aiogram import Router, F, types, Bot
from aiogram.filters import Command, StateFilter
from src.logger import setup_logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.database.orm.shops import create_global_shop, cancel_slot, create_local_shop, get_wifes_for_user, create_slot, get_all_slots_from_shop, get_wife_from_slot, get_slot, purchase_slot, get_my_slots
from src.database.models import ShopTypes
from src.database.orm.wifes import get_character
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from more_itertools import chunked
from src.bot.keyboards.inline.pagination_kb import pagination_kb

import os


router = Router()
logger = setup_logger(__name__)



@router.message(Command("shop"))
async def mess_shop(message: types.Message, state: FSMContext):
    await shop_open(message=message, state=state, mess=True)


@router.callback_query(F.data == "shop")
async def call_shop(callback: types.CallbackQuery, state: FSMContext):
    await shop_open(message=callback.message, state=state)


async def shop_open(message: types.Message|types.CallbackQuery, state: FSMContext, mess=False):
    await state.clear()
    if message.chat.type == "private":
        # В боте
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Глобальный", callback_data="global_shop")],
                [InlineKeyboardButton(text="Создать лот", callback_data="create_auction")],
                [InlineKeyboardButton(text="Мои лоты", callback_data="my_lots")]
            ]
        )
    else:
        # В чате
        shop = await create_local_shop(chat_id=message.chat.id,
                                type=ShopTypes.LOCAL)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Глобальный", callback_data="global_shop"), InlineKeyboardButton(text="Локальный", callback_data="local_shop")],
                [InlineKeyboardButton(text="Создать лот", callback_data="create_auction")],
                [InlineKeyboardButton(text="Мои лоты", callback_data="my_lots")]
            ]
        )

    await message.answer("Какой рынок вас интересует:", reply_markup=keyboard)


class ShopList(StatesGroup):
    selecting_wife = State()
    page = State()

    max_pages = State()
    pages = State()
    use_user_id = State()


@router.callback_query(F.data == "my_lots")
async def my_lots(callback: types.CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    slots = await get_my_slots(user_id=user_id)

    chunks = list(chunked(slots, 5))
    await state.set_state(ShopList.page)
    await state.update_data(page=1, max_pages=len(chunks), pages=chunks, use_user_id=user_id)

    if len(chunks) > 0:
        await callback.message.answer("Ваши лоты:", reply_markup=await pagination_kb(page=1, list_slots=chunks[0], max_page=len(chunks), user_id=user_id, my_slots=True))
    else:
        await callback.message.answer("Рынок пуст")


@router.callback_query(F.data.startswith("stop_select_"), StateFilter(ShopList))
async def my_lot_select(callback: types.CallbackQuery, state: FSMContext):
    callback_data = callback.from_user.id
    data = await state.get_data()
    
    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return

    callback_data = callback.data.split("_")[-1]
    await state.update_data(slot_id=callback_data)
    character = await get_wife_from_slot(slot_id=int(callback_data))
    slot = await get_slot(id=int(callback_data))

    user_id = callback.from_user.id

    user_photo_path = f"./media/wifes/{character.id}/profile.png"
    default_photo_path = "./media/wifes/default.png"

    if os.path.exists(user_photo_path) and os.path.isfile(user_photo_path):
        photo = types.FSInputFile(path=user_photo_path)
    else:
        photo = types.FSInputFile(path=default_photo_path)

    
    if character:
        await state.update_data(selecting_wife=character.id)

        await callback.message.answer_photo(photo=photo, caption=f"👨Ваш лот: \n🆔 {character.id} \n👤Полное имя: {character.name} \n🌸 Тайтл: {character.from_[:120]}\n💎Редкость: {character.rare.value}\nЦена-💠{slot.price}",
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                            [InlineKeyboardButton(text="Снять с продажи", callback_data=f"stop_selling_{data["use_user_id"]}_{callback_data}")]
                                        ]))
    else:
        await callback.message.answer("Товар уже был продан.")


@router.callback_query(F.data.startswith("stop_selling_"), StateFilter(ShopList))
async def stop_selling_lot(callback: types.CallbackQuery, state: FSMContext):
    callback_data = callback.from_user.id
    data = await state.get_data()
    
    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    
    user_id = callback.from_user.id
    callback_data = callback.data.split("_")[-1]
    await state.update_data(slot_id=callback_data)

    status = await cancel_slot(seller_user_id=int(callback.data.split("_")[2]), slot_id=int(data["slot_id"]))

    if status["status"] == "success":
        await callback.message.answer("Лот успешно закрыт.")
    else:
        await callback.message.answer("Лот Не удалось закрыть.")
        

@router.callback_query(F.data == "global_shop")
async def global_shop(callback: types.CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    slots = await get_all_slots_from_shop(chat_id=1)

    chunks = list(chunked(slots, 5))
    await state.set_state(ShopList.page)

    await state.update_data(page=1, max_pages=len(chunks), pages=chunks, use_user_id=user_id)

    if len(chunks) > 0:
        await callback.message.answer("Глобальный рынок:", reply_markup=await pagination_kb(page=1, list_slots=chunks[0], max_page=len(chunks), user_id=user_id))
    else:
        await callback.message.answer("Рынок пуст")


@router.callback_query(F.data == "local_shop")
async def local_shop(callback: types.CallbackQuery, state: FSMContext):
    chat_id = callback.message.chat.id
    user_id = callback.from_user.id
    slots = await get_all_slots_from_shop(chat_id=chat_id)

    chunks = list(chunked(slots, 5))
    await state.set_state(ShopList.page)

    await state.update_data(page=1, max_pages=len(chunks), pages=chunks, use_user_id=user_id)
    if len(chunks) > 0:
        await callback.message.answer("Ваш локальный рынок:", reply_markup=await pagination_kb(page=1, list_slots=chunks[0], max_page=len(chunks), user_id=user_id))
    else:
        await callback.message.answer("Рынок пуст")


@router.callback_query(F.data.startswith("shop_refresh_"), StateFilter(ShopList))
async def shop_refresh(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    callback_data = callback.from_user.id

    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    chat_id = callback.message.chat.id
    page = data["page"]
    slots = await get_all_slots_from_shop(chat_id=chat_id)

    chunks = list(chunked(slots, 5))

    await state.update_data(page=page, max_pages=len(chunks), pages=chunks)
    await callback.message.delete()
    await callback.message.answer(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=len(chunks),
                                                                                          list_slots=chunks[page - 1], user_id=callback_data))

@router.callback_query(lambda query: "shop_right_pagination_" in query.data, StateFilter(ShopList))
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
    await callback.message.edit_text(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=max_pages, list_slots=pages[page-1]))


@router.callback_query(lambda query: "shop_left_pagination_" in query.data, StateFilter(ShopList))
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
    await callback.message.edit_text(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=max_pages, list_slots=pages[page-1]))


@router.callback_query(F.data.startswith("buy_"), StateFilter(ShopList))
async def buy_character(callback: types.CallbackQuery, state: FSMContext):
    callback_data = callback.from_user.id
    await state.update_data(slot_id=callback_data)
    data = await state.get_data()
    
    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return

    callback_data = callback.data.split("_")[-1]
    character = await get_wife_from_slot(slot_id=int(callback_data))
    slot = await get_slot(id=int(callback_data))

    user_id = callback.from_user.id

    user_photo_path = f"./media/wifes/{character.id}/profile.png"
    default_photo_path = "./media/wifes/default.png"

    if os.path.exists(user_photo_path) and os.path.isfile(user_photo_path):
        photo = types.FSInputFile(path=user_photo_path)
    else:
        photo = types.FSInputFile(path=default_photo_path)

    
    if character:
        await state.update_data(selecting_wife=character.id)

        await callback.message.answer_photo(photo=photo, caption=f"👨Персонаж для покупки: \n🆔 {character.id} \n👤Полное имя: {character.name} \n🌸 Тайтл: {character.from_[:120]}\n💎Редкость: {character.rare.value}\nЦена-💠{slot.price}",
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                            [InlineKeyboardButton(text="Купить", callback_data=f"this_buy_{character.id}_{callback_data}")]
                                        ]))
    else:
        await callback.message.answer("Товар уже был продан.")


@router.callback_query(F.data.startswith("this_buy_"), StateFilter(ShopList))
async def buy_character(callback: types.CallbackQuery, state: FSMContext):
    callback_data = callback.data.split("_")
    slot_id = int(callback_data[-1])
    user_id = callback.from_user.id

    # try:

    await callback.message.delete()
    status = await purchase_slot(slot_id=slot_id, buyer_user_id=user_id)

    if status["status"] == "success":
        await callback.message.answer("Покупка удалась! 🎉")
        await state.clear()
    else:
        await callback.message.answer(f"Ошибка: {status['message']} 😔")
        await state.clear()

    # except Exception as e:
    #     await callback.message.delete()
    #     await callback.message.answer(f"Произошла ошибка: {str(e)}")


class CreateAuctionStates(StatesGroup):
    selecting_wife = State()
    entering_price = State()
    selecting_market = State()
    
    page = State()
    max_pages = State()
    pages = State()
    use_user_id = State()


@router.callback_query(F.data == "create_auction")
async def create_auction(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    message_id = callback.message.message_id
    wifes = await get_wifes_for_user(user_id=user_id)
    chat_id = callback.message.chat.id

    await state.set_state(CreateAuctionStates.page)

    chunks = list(chunked(wifes, 5))
    await state.update_data(page=1, max_pages=len(chunks), pages=chunks, use_user_id=user_id)
    try:
        await callback.message.answer("Все ваши персонажи:", reply_markup=await pagination_kb(page=1, list_requests=chunks[0], max_page=len(chunks), user_id=user_id))
    except:
        await callback.message.answer("У вас нет персонажей")

@router.callback_query(lambda query: "refresh_" in query.data, StateFilter(CreateAuctionStates))
async def refresh(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    callback_data = callback.data.split("_")[-1]

    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return
    page = data["page"]
    wifes = await get_wifes_for_user(user_id=callback.from_user.id)

    chunks = list(chunked(wifes, 5))

    await state.update_data(page=page, max_pages=len(chunks), pages=chunks)
    await callback.message.delete()
    await callback.message.answer(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=len(chunks),
                                                                                          list_requests=chunks[page - 1], user_id=callback_data))
    

@router.callback_query(lambda query: "right_pagination_" in query.data, StateFilter(CreateAuctionStates))
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
    await callback.message.edit_text(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=max_pages, list_requests=pages[page-1]))


@router.callback_query(lambda query: "left_pagination_" in query.data, StateFilter(CreateAuctionStates))
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
    await callback.message.edit_text(text="Все заявки:", reply_markup=await pagination_kb(page=page, max_page=max_pages, list_requests=pages[page-1]))


@router.callback_query(lambda query: "select_" in query.data, StateFilter(CreateAuctionStates))
async def select(callback: types.CallbackQuery, bot: Bot, state: FSMContext):
    data = await state.get_data()
    callback_data = callback.data.split("_")[1]
    
    if int(callback_data) != int(data["use_user_id"]):
        await callback.answer(f"@{callback.from_user.username} ты не можешь трогать персонажей другого человека")
        return

    callback_data = callback.data.split("_")[-1]
    user_id = callback.from_user.id

    user_photo_path = f"./media/wifes/{callback_data}/profile.png"
    default_photo_path = "./media/wifes/default.png"

    if os.path.exists(user_photo_path) and os.path.isfile(user_photo_path):
        photo = types.FSInputFile(path=user_photo_path)
    else:
        photo = types.FSInputFile(path=default_photo_path)

    character = await get_character(id=int(callback_data))
    if character:
        await state.update_data(selecting_wife=character.id)

        await callback.message.answer_photo(photo=photo, caption=f"👨Персонаж для продажи: \n🆔 {character.id} \n👤Полное имя: {character.name} \n🌸 Тайтл: {character.from_[:120]}\n💎Редкость: {character.rare.value}",
                                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                            [InlineKeyboardButton(text="Выставить на продажу", callback_data=f"on_slot_{character.id}")]
                                        ]))
    else:
        await callback.message.answer("🤷‍♀️Не удалось выставить персонажа, возможно он в обмене или уже на продаже.")


@router.callback_query(lambda query: "on_slot_" in query.data, StateFilter(CreateAuctionStates))
async def set_price(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Укажите цену")
    await state.set_state(CreateAuctionStates.entering_price)


def contains_only_digits(text: str) -> bool:
    return text.isdigit()


@router.message(F.text, StateFilter(CreateAuctionStates.entering_price))
async def price_detected(message: types.Message, state: FSMContext):
    data = await state.get_data()
    callback_data = message.from_user.id
    
    if int(callback_data) != int(data["use_user_id"]):
        return
    
    text = message.text
    if contains_only_digits(text=text):
        await state.update_data(price=text)
        if message.chat.type == "private":
            await message.answer("Выберите тип чата:", 
                                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                    [InlineKeyboardButton(text="Глобальный", callback_data="to_shop_global")],
                                ]))
        else:
            await message.answer("Выберите тип чата:", 
                                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                        [InlineKeyboardButton(text="Глобальный", callback_data="to_shop_global")],
                                        [InlineKeyboardButton(text="Локальный", callback_data="to_shop_local")]
                                    ]))
    else:
        await message.answer("Цена💠 указывается числами")


@router.callback_query(lambda query: "to_shop_" in query.data)
async def finish_slot(callback: types.CallbackQuery, state: FSMContext):
    callback_data = callback.data.split("_")[-1]

    data = await state.get_data()
    user_id = data["use_user_id"]
    wife_id = data["selecting_wife"]
    price = data["price"]
    await callback.message.delete()

    if callback_data == "local":
        chat_id = callback.message.chat.id
        shop = await create_local_shop(chat_id=chat_id, type=ShopTypes.LOCAL)

        slot = await create_slot(
            user_id=user_id,
            wife_id=wife_id,
            shop_id=shop.id,
            price=price,
        )

        await callback.message.answer(f"✅@{callback.from_user.username} ваш лот под id - {slot.id} выставлен на продажу")

    if callback_data == "global":
        shop = await create_global_shop()

        slot = await create_slot(
            user_id=user_id,
            wife_id=wife_id,
            shop_id=shop.id,
            price=price,
        )
        await callback.message.answer(f"✅@{callback.from_user.username} ваш лот под id - {slot.id} выставлен на продажу")
    await state.clear()
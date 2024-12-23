from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from src.redis.services import redis_manager
from src.database.orm.wifes import add_random_wifes_to_redis, get_character
from aiogram.filters import Command, StateFilter
import datetime
from src.database.models import Wife, AllRares
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.database.orm.users import create_user
from aiogram.fsm.state import State, StatesGroup


router = Router()


class EverydayShop(StatesGroup):
    shop = State()

@router.message(Command("everyday_shop"))
async def everyday_shop(message: types.Message, state: FSMContext):
    await add_random_wifes_to_redis(user_id=message.from_user.id)
    await state.clear()
    await state.set_state(EverydayShop.shop)
    redis_client = await redis_manager.get_redis()
    # Получаем текущую дату в формате YYYY-MM-DD
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    redis_key = f"shop:{current_date}:{message.from_user.id}"

    # Получаем данные из Redis
    shop_data = await redis_client.hgetall(redis_key)

    if not shop_data:
        await message.answer("Магазин пуст. Попробуйте позже.")
        return

    # Формируем сообщение с товарами
    user_data = await create_user(data={
        "user_id": message.from_user.id
    })
    message_text = f"{message.from_user.username}, ваш баланс - 🔰{user_data.get("data").alter_balance}\nЕжедневный магазин:\n"
    kb = []
    for rarity, wife_id in shop_data.items():
        wife_id = int(wife_id)
        wife = await get_character(id=wife_id)
        if wife:
            if wife.rare == AllRares.SIMPLE:
                price = 10
                rare = "⚪️"
      
            if wife.rare == AllRares.RARE:
                price = 15
                rare = "🟢"

            if wife.rare == AllRares.EPIC:
                price = 20
                rare = "🟣"

            if wife.rare == AllRares.LEGENDARY:
                price = 30
                rare = "🟠"
            

            response = f"{wife.name} - {rare}{wife.rare.value} - 🔰{price} | (ID: {wife.id})\n"
            kb.append([InlineKeyboardButton(text=response, callback_data=f"everaday_shop_{price}_{wife.id}")])
    kb.append([InlineKeyboardButton(text="🔄 Обновить", callback_data=f"refresh")])

    await message.answer(message_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))


@router.callback_query(F.data == "refresh", StateFilter(EverydayShop))
async def shop_refresh(callback: types.CallbackQuery, state: FSMContext):
    await add_random_wifes_to_redis(user_id=callback.from_user.id, refresh=True)
    
    await state.set_state(EverydayShop.shop)
    redis_client = await redis_manager.get_redis()
    # Получаем текущую дату в формате YYYY-MM-DD
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    redis_key = f"shop:{current_date}:{callback.from_user.id}"

    # Получаем данные из Redis
    shop_data = await redis_client.hgetall(redis_key)

    if not shop_data:
        await callback.message.answer("Магазин пуст. Попробуйте позже.")
        return

    # Формируем сообщение с товарами
    user_data = await create_user(data={
        "user_id": callback.from_user.id
    })
    message_text = f"{callback.from_user.username}, ваш баланс - 🔰{user_data.get("data").alter_balance}\nЕжедневный магазин:\n"
    kb = []
    for rarity, wife_id in shop_data.items():
        wife_id = int(wife_id)
        wife = await get_character(id=wife_id)
        if wife:
            if wife.rare == AllRares.SIMPLE:
                price = 10
                rare = "⚪️"
      
            if wife.rare == AllRares.RARE:
                price = 15
                rare = "🟢"

            if wife.rare == AllRares.EPIC:
                price = 20
                rare = "🟣"

            if wife.rare == AllRares.LEGENDARY:
                price = 30
                rare = "🟠"

            response = f"{wife.name} - {rare}{wife.rare.value} - 🔰{price} | (ID: {wife.id})\n"
            kb.append([InlineKeyboardButton(text=response, callback_data=f"everaday_shop_{price}")])
    kb.append([InlineKeyboardButton(text="Обновить", callback_data=f"refresh")])

    await callback.message.answer(message_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb))


@router.callback_query(F.data.startswith("everaday_shop_"), StateFilter(EverydayShop))
async def buy_from_everyday_shop(callback: types.CallbackQuery):
    
from aiogram import Router, F, types
from aiogram.filters import Command
from src.logger import setup_logger
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from src.database.orm.shops import create_local_shop
from src.database.models import ShopTypes

router = Router()
logger = setup_logger(__name__)


@router.message(F.text == "!рынок")
@router.message(F.text == "Рынок")
@router.message(Command("/shop"))
async def shop_open(message: types.Message):
    if message.chat.type == "private":
        # В боте
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Глобальный", callback_data="global_shop")],
                [InlineKeyboardButton(text="Создать лот", callback_data="create_auction")]
            ]
        )
    else:
        # В чате
        shop = await create_local_shop(chat_id=message.chat.id,
                                type=ShopTypes.LOCAL)

        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Глобальный", callback_data="global_shop"), InlineKeyboardButton(text="Локальный", callback_data="local_shop")],
                [InlineKeyboardButton(text="Создать лот", callback_data="create_auction")]
            ]
        )

    await message.answer("Какой рынок вас интересует:", reply_markup=keyboard)


@router.callback_query(F.data == "global_shop")
async def global_shop(callback: types.CallbackQuery):
    await callback.message.answer("Тут пока пусто")


@router.callback_query(F.data == "local_shop")
async def local_shop(callback: types.CallbackQuery):
    await callback.message.answer("Тут пока пусто")


@router.callback_query(F.data == "create_auction")
async def create_auction(callback: types.CallbackQuery):
    await callback.message.answer("Создание нового лота...")
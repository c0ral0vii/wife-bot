from aiogram import Router, F, types, Bot
from aiogram.filters import StateFilter, Command
from src.database.orm.trade import answer_trade
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from src.logger import setup_logger
from src.bot.keyboards.inline.pagination_kb import pagination_kb
from src.database.orm.shops import get_wifes_for_user


router = Router()
logger = setup_logger(__name__)


class TradeState(StatesGroup):
    use_user_id = State()
    to_user_id = State()

    page = State()
    max_page = State()
    pages = State()


@router.message(Command("trade"))
async def trade(message: types.Message, bot: Bot, state: FSMContext):
    text = message.text.split(" ")

    if len(text) != 2:
        await message.answer("Вот так выглядит обмен - /trade <user_id>")
    
    user_id = message.from_user.id
    characters = await get_wifes_for_user(user_id=user_id)

    await state.set_state(TradeState.use_user_id)
    await state.update_data(use_user_id=user_id)

    await message.answer("Учтите получить одинаковых персонажей дважды нельзя\n\nВаши персонажи для обмена:", reply_markup=await pagination_kb())
    


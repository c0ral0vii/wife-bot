from aiogram import Router, types, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from src.logger import setup_logger
from src.bot.keyboards.reply import start_kb
from src.database.orm.users import check_vip, create_user
from src.database.orm.promo import get_promo
from src.utils.create_file import create_file_profile
from src.bot.fsm.promo import Promo


router = Router(name='start_router')
logger = setup_logger(__name__)


@router.message(CommandStart())
async def start_command(message: types.Message):

    user = await create_user(data={
        "user_id": message.from_user.id,
        "username": message.from_user.username,
    })
    
    await create_file_profile(
        file_name=message.from_user.id
    )

    await message.answer(text="""Привет, с помошью меня, вы можете собрать множество wife из самых различных манг/аниме/игр.\nВы можете продавать или обменивать их на глобальном рынке или в своем локальном""", reply_markup=await start_kb.start_kb())
    

@router.message(Command("help"))
async def help_command(message: types.Message):
    await message.answer("""Команда помощи""")


@router.message(Command("promo"))
async def promo_command(message: types.Message, state: FSMContext):
    await state.set_state(Promo.promo)
    await message.answer("""Введите промокод""")


@router.message(F.text, Promo.promo)
async def check_promo(message: types.Message, state: FSMContext):

    result = await get_promo(promocode=message.text)

    if result is None:
        await message.answer("Такого промокода не существует")
    else:
        await message.answer(f"Вы ввели промокод на {result} бонусов")
        
    await state.clear()
from aiogram import Router, F, types
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from src.bot.middlewares.admin_middleware import AdminMiddleware
from src.database.models import UserStatus
from src.database.orm.vip_users import set_vip_status
from src.logger import setup_logger

router = Router()

router.message.middleware(AdminMiddleware())
router.callback_query.middleware(AdminMiddleware())


class AddVipUser(StatesGroup):
    add_vip = State()
    user_id = State()


@router.callback_query(F.data == "add_vip")
async def add_vip_user(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddVipUser.user_id)
    await callback_query.message.answer("Выберите уровень VIP для пользователя:",
                                        reply_markup=types.InlineKeyboardMarkup(
                                            inline_keyboard=[
                                                [types.InlineKeyboardButton(text="1-й VIP", callback_data="add_vip_1"),],
                                                [types.InlineKeyboardButton(text="2-й VIP", callback_data="add_vip_2"),],
                                                [types.InlineKeyboardButton(text="3-й VIP", callback_data="add_vip_3"),],
                                            ]
                                        ))

logger = setup_logger(__name__)
@router.callback_query(F.data.startswith("add_vip_"), StateFilter(AddVipUser.user_id))
async def add_vip_1(callback_query: types.CallbackQuery, state: FSMContext):
    await state.set_state(AddVipUser.add_vip)
    callback_data = int(callback_query.data.split("_")[-1])
    logger.debug(callback_data)
    if  callback_data == 1:
        vip_status = UserStatus.BASE_VIP
    elif callback_data == 2:
        vip_status = UserStatus.MIDDLE_VIP
    elif callback_data == 3:
        vip_status = UserStatus.SUPER_VIP
    else:
        vip_status = UserStatus.MIDDLE_VIP

    await state.update_data(vip_status=vip_status)

    await callback_query.message.answer("Отправь user_id пользователя")


@router.message(F.text, StateFilter(AddVipUser.add_vip))
async def add_vip(message: types.Message, state: FSMContext):
    user_id = message.text
    data = await state.get_data()
    try:
        await set_vip_status(user_id=int(user_id), vip_status=data["vip_status"])

        await message.answer("Вип выдан пользователю")
        await state.clear()
    except ValueError:
        await message.answer("Такой пользователь не найден")
        await state.clear()
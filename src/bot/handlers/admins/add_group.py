import asyncio

from aiogram import Router, F, types, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from src.bot.middlewares.admin_middleware import AdminMiddleware
from src.database.orm.groups import create_group, delete_group_db, get_groups, get_random_group
from src.logger import setup_logger
from src.spammer.services import SpammerService

router = Router()
logger = setup_logger(__name__)

router.message.middleware(AdminMiddleware())
router.callback_query.middleware(AdminMiddleware())


class AddGroup(StatesGroup):
    group = State()
    group_link = State()
    delete_group = State()


@router.callback_query(F.data == "add_group")
async def add_group_call(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AddGroup.group)
    await callback.message.answer("Перешли сообщение из группы")


@router.message(F.text, StateFilter(AddGroup.group))
async def add_group_text(message: types.Message, state: FSMContext, bot: Bot):

    group = message.text
    if not message.forward_from_chat:
        await message.answer("Это не пересланное сообщение с группы")
        return

    chat_id = message.forward_from_chat.id
    try:
        get_user = await bot.get_chat_member(chat_id=f"{chat_id}", user_id=bot.id)
        await state.update_data(chat_id=chat_id)

        await message.answer("Вышли пригласительную ссылку на группу")
        await state.set_state(AddGroup.group_link)

    except:
        await message.answer("Я не админ в этом канале, не могу проверять подписался ли человек или нет \n\nЧтобы я работал мне нужно разрешение в группе на 'Добавление подписчиков'")
        return


@router.message(F.text, StateFilter(AddGroup.group_link))
async def add_group_link(message: types.Message, state: FSMContext, bot: Bot):
    group_link = message.text

    if "t.me" not in group_link:
        await message.answer("Это не ссылка на группу")
        return

    data = await state.get_data()

    result = await create_group(
        chat_id=data["chat_id"],
        join_link=group_link,
    )

    await message.answer(result["message"])
    await state.clear()


@router.callback_query(F.data == "remove_group")
async def delete_group(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте пригласительную ссылку для удаления")
    await state.set_state(AddGroup.delete_group)


@router.message(F.text, StateFilter(AddGroup.delete_group))
async def already_deleted(message: types.Message, state: FSMContext, bot: Bot):
    group = message.text

    result = await delete_group_db(group)

    await message.answer(result["message"])
    await state.clear()


@router.callback_query(F.data == "list_group")
async def group_list(callback: CallbackQuery, state: FSMContext):
    groups = await get_groups()
    message_text = "Все группы:"


    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{group.group_link}({group.chat_id})", callback_data=f"nothing")]
            for group in groups
        ]
    )

    await callback.message.answer(message_text, reply_markup=keyboard)


@router.callback_query(F.data == "send_all")
async def send_to_all(message: types.Message, state: FSMContext, bot: Bot):
    await message.answer("Рассылка началась")
    user_id = message.from_user.id
    spam = SpammerService()

    asyncio.create_task(spam.spam(bot=bot, user_id=user_id))
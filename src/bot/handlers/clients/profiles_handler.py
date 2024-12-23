import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from src.database.orm.users import get_user, get_count_wifes, change_nickname
from src.bot.fsm.change_profile import ChangeProfile
from src.logger import setup_logger

router = Router()
logger = setup_logger(__name__)


from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import os

router = Router()

@router.message(F.text == "👤 Профиль")
@router.message(Command("profile"))
async def get_profile(message: types.Message, state: FSMContext):
    await handle_profile(message_or_callback=message, state=state, message=True, user_id=message.from_user.id)

@router.callback_query(F.data == "profile")
async def get_profile_callback(callback: types.CallbackQuery, state: FSMContext):
    await handle_profile(message_or_callback=callback.message, state=state, user_id=callback.from_user.id)


def contains_only_digits(text: str) -> bool:
    return text.isdigit()


async def handle_profile(message_or_callback, user_id: int, state: FSMContext, message: bool = False):
    dont_change = False

    if message:
        text = message_or_callback.text.split(" ")
        if len(text) >= 2 and contains_only_digits(text=text[-1]):
            dont_change = True
            user_id = int(text[-1])

        if message_or_callback.reply_to_message:
            dont_change = True
            user_id = message_or_callback.reply_to_message.from_user.id
    
    user_data = await get_user(user_id=user_id)

    if not user_data:
        await message_or_callback.answer("У вас нет профиля, перейдите в бота и создайте его")
        return

    count = await get_count_wifes(user=user_data)
    user_photo_path = f"./media/profiles/{user_id}/profile.png"
    default_photo_path = "./media/profiles/default/default.png"

    if os.path.exists(user_photo_path) and os.path.isfile(user_photo_path):
        photo = types.FSInputFile(path=user_photo_path)
    else:
        photo = types.FSInputFile(path=default_photo_path)

    if not message_or_callback.chat.type == "private" or dont_change:
        # В боте
        await message_or_callback.answer_photo(photo=photo, caption=f"""{user_data.username}, ваш профиль:\nUID {user_data.user_id}\n\nСтатус - {user_data.status.value}\n\n🏰 Гарем: {count.get("my_total", 0)}/{count.get("total_counts", 0)} ({count.get("my_total_percent", 0):.1f}%)\n\
                                   \n⚪️ {count.get("my_simple", 0)}/{count.get("total_simple", 0)} ({count.get("my_simple_percent", 0):.1f}%)\
                                    \n🟢 {count.get("my_rare", 0)}/{count.get("total_rare", 0)} ({count.get("my_rare_percent", 0):.1f}%)\
                                    \n🟣 {count.get("my_epic", 0)}/{count.get("total_epic", 0)}  ({count.get("my_epic_percent", 0):.1f}%)\
                                    \n🟠 {count.get("my_legendary", 0)}/{count.get("total_legendary", 0)} ({count.get("my_legendary_percent", 0):.1f}%) 
                                   """)
    else:
        await message_or_callback.answer_photo(photo=photo, caption=f"""{user_data.username}, ваш профиль:\nUID {user_data.user_id}\n\nСтатус - {user_data.status.value}\n\n🏰 Гарем: {count.get("my_total", 0)}/{count.get("total_counts", 0)} ({count.get("my_total_percent", 0):.1f}%)\n\
                                   \n⚪️ {count.get("my_simple", 0)}/{count.get("total_simple", 0)} ({count.get("my_simple_percent", 0):.1f}%)\
                                    \n🟢 {count.get("my_rare", 0)}/{count.get("total_rare", 0)} ({count.get("my_rare_percent", 0):.1f}%)\
                                    \n🟣 {count.get("my_epic", 0)}/{count.get("total_epic", 0)}  ({count.get("my_epic_percent", 0):.1f}%)\
                                    \n🟠 {count.get("my_legendary", 0)}/{count.get("total_legendary", 0)} ({count.get("my_legendary_percent", 0):.1f}%)
                                   """, 
                                   reply_markup=InlineKeyboardMarkup(
                                       inline_keyboard=[
                                           [InlineKeyboardButton(text="Изменить фотографию", callback_data="change_image")],
                                           [InlineKeyboardButton(text="Поменять никнейм", callback_data="change_nickname")]
                                       ]
                                   ))
        
    
@router.callback_query(F.data == "change_image")
async def change_profile_img(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте ваше фото")
    await state.set_state(ChangeProfile.new_photo)


@router.message(ChangeProfile.new_photo, F.content_type == "photo")
async def new_photo(message: types.Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1] 
    file_id = photo.file_id

    file_path = await bot.get_file(file_id)
    await bot.download_file(file_path.file_path, f"./media/profiles/{message.from_user.id}/profile.png")
    
    await message.answer("Фотография успешно обновлена!")

    await state.clear()


@router.callback_query(F.data == "change_nickname")
async def change_profile_img(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer("Отправьте новый никнейм")
    await state.set_state(ChangeProfile.username)


@router.message(ChangeProfile.username, F.text)
async def new_username(message: types.Message, state: FSMContext, bot: Bot):
    try:
        text = message.text

        await change_nickname(user_id=message.from_user.id, new_username=text)
        await message.answer("Никнейм успешно обновлен!")
        await state.clear()
    except Exception as e:
        await message.answer("Не удалось обновить никнейм, попробуйте другое имя.")
        await state.clear()




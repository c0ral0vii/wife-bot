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


@router.message(F.text.lower() == "!профиль")
@router.message(F.text == "Профиль")
@router.message(Command("/profile", "!profile"))
async def get_profile(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = await get_user(user_id=user_id)

    # username_query = message.get_args()  # Получаем аргументы после команды
    # if username_query:
    #     # Если есть username, ищем его профиль
    # else:
    #     # Иначе ищем профиль текущего пользователя
    #     user_data = await get_user(user_id=user_id)


    if not user_data:
        await message.answer("У вас нет профиль, перейдите в бота и создайте его")
        
    count = await get_count_wifes(user=user_data)
    user_photo_path = f"./media/profiles/{user_id}/profile.png"
    default_photo_path = "./media/profiles/default/default.png"

    if os.path.exists(user_photo_path) and os.path.isfile(user_photo_path):
        photo = types.FSInputFile(path=user_photo_path)
    else:
        photo = types.FSInputFile(path=default_photo_path)
    
    if not message.chat.type == "private":
        # В боте
        await message.answer_photo(photo=photo, caption=f"Ваше имя - {user_data.username}\n\nВаш статус - {user_data.status.value}\n\nБаланс - {user_data.balance}\nКоличество персонажей - {count.get("total_wifes", 0)}")
    else:
        await message.answer_photo(photo=photo, caption=f"Ваше имя - {user_data.username}\n\nВаш статус - {user_data.status.value}\n\nБаланс - {user_data.balance}\nКоличество персонажей - {count.get("total_wifes", 0)}", 
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




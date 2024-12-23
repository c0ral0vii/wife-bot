from aiogram import Router, F, types
from src.database.orm.users import check_user_has_wife
import shutil
import os

router = Router()



@router.callback_query(F.data.startswith("set_on_photo_"))
async def set_on_photo(callback: types.CallbackQuery):
    callback_data = callback.data.split("_")[-1]
    user_id = callback.from_user.id

    # Проверяем, есть ли у пользователя эта вайфа
    result = await check_user_has_wife(wife_id=int(callback_data), user_id=int(user_id))

    if result:
        # Путь к новому изображению
        from_path = f"./media/wifes/{callback_data}/profile.png"

        # Проверяем, существует ли файл
        if not os.path.exists(from_path):
            # Если файл не существует, используем изображение по умолчанию
            from_path = f"./media/wifes/default.png"

        # Удаляем старое изображение, если оно существует
        old_profile_path = f"./media/profiles/{user_id}/profile.png"
        if os.path.exists(old_profile_path):
            os.remove(old_profile_path)

        # Копируем новое изображение
        shutil.copy2(from_path, old_profile_path)

        await callback.answer("Фотография установлена")
    else:
        await callback.answer("У вас нет этой вайфы")
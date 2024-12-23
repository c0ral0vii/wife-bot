from aiogram import Router, F, types
from aiogram.filters import Command
from decimal import Decimal
from src.logger import setup_logger
from src.redis.services import redis_manager
from src.database.orm.users import add_balance


router = Router(name="get_bonus")
logger = setup_logger(__name__)


import time
from datetime import timedelta

@router.message(F.text == "🎁 Получить бонус")
@router.message(Command("bonus"))
async def get_bonus(message: types.Message):
    user_id = message.from_user.id
    key = f"user:{user_id}:bonus"

    # Получаем время последнего получения бонуса из Redis
    last_bonus_time = await redis_manager.get(key)

    if last_bonus_time:
        try:
            # Пробуем преобразовать значение в int (timestamp)
            last_bonus_time = int(last_bonus_time)
        except ValueError:
            # Если значение не является timestamp, удаляем ключ (например, если там была строка "Не прошло 2 часа")
            await redis_manager.delete(key)
            last_bonus_time = None

    if last_bonus_time:
        # Вычисляем оставшееся время
        remaining_time = 7200 - (int(time.time()) - last_bonus_time)
        if remaining_time > 0:
            # Преобразуем оставшееся время в формат часов, минут и секунд
            delta = timedelta(seconds=remaining_time)
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            await message.answer(f"⌛️ Бонус будет доступен через: {hours}ч {minutes}м {seconds}с")
            return

    try:
        # Устанавливаем текущее время в Redis с TTL 2 часа
        await redis_manager.set_with_ttl(key=key, value=str(int(time.time())), ttl=7200)

        value = 1000
        added = await add_balance(
            user_id=user_id,
            add_to=Decimal(value),
        )
        await message.answer(f"🎁 {message.from_user.id}, Вы получили 💠{added['value']}, теперь у вас 💠{added['balance']} \
\n⌛️ Можно забрать снова через: 2 часа")
    except Exception as e:
        logger.error(e)
        await message.answer("Попробуйте еще раз")
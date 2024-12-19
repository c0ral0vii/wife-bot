from aiogram import Router, F, types
from aiogram.filters import Command
from decimal import Decimal
from src.logger import setup_logger
from src.redis.services import redis_manager
from src.database.orm.users import add_balance


router = Router(name="get_bonus")
logger = setup_logger(__name__)


@router.message(F.text == "!бонус")
@router.message(F.text == "Получить бонус")
@router.message(Command("bonus"))
async def get_bonus(message: types.Message):
    user_id = message.from_user.id
    status = await redis_manager.get(f"user:{user_id}:bonus")

    if status == "Не прошло 2 часа":
        await message.answer(text="⌛️ Бонус активен каждые: 2 часа")
    else:
        try:
            await redis_manager.set_with_ttl(key=f"user:{user_id}:bonus", value="Не прошло 2 часа", ttl=7200)
            value = 1000
            added = await add_balance(
                user_id=user_id,
                add_to=Decimal(value),
            )
            await message.answer(f"🎁 Елизабет, Вы получили 💠{added['value']}, теперь у вас 💠{added['balance']} \
\n⌛️ Можно забрать снова через: 2 часа")
        except Exception as e:
            logger.error(e)
            await message.answer("Попробуйте еще раз")
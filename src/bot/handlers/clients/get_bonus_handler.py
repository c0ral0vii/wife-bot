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

    if status == "Не прошло 1 часа":
        await message.answer(text="Вы еще не можете получить бонус\nБонус получается каждый час")
    else:
        try:
            await redis_manager.set_with_ttl(key=f"user:{user_id}:bonus", value="Не прошло 1 часа", ttl=3600)
            await add_balance(
                user_id=user_id,
                add_to=Decimal('1000.00')
            )
            await message.answer("Вам начислено 1000 бонусов\nСледующий бонус через час!")
        except Exception as e:
            logger.error(e)
            await message.answer("Попробуйте еще раз")
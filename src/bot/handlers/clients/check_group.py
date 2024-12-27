from decimal import Decimal

from aiogram import Router, types, F

from src.database.orm.groups import get_group
from src.database.orm.users import add_balance
from src.redis.services import redis_manager


router = Router()


@router.callback_query(F.data.startswith("sub_"))
async def check_sub(callback_query: types.CallbackQuery):
    group_id = callback_query.data.split("_")[-1]
    redis_key = f"sub:{callback_query.from_user.id}:{group_id}"

    get_redis = await redis_manager.get(key=redis_key)
    if get_redis:
        await callback_query.message.answer("Вы уже получали бонус от этой группы!")
        return

    group = await get_group(group_id=int(group_id))
    await add_balance(user_id=callback_query.from_user.id, add_to=group["data"].bonus)
    await redis_manager.set_with_ttl(key=redis_key, value="use", ttl=604800)

    await callback_query.message.answer(group["message"])
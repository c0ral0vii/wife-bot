from decimal import Decimal
from typing import Dict, Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from src.database.database import async_session
from src.database.models import User, Wife


async def purchaser(price: int | Decimal, wife_id: int, user_id: int) -> Dict[str, Any]:
    async with async_session() as session:
        try:
            stmt = select(User).options(selectinload(User.characters)).where(User.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user is None:
                return {
                    "message": "Создайте профиль в боте"
                }

            if isinstance(price, int):
                price = Decimal(price)

            user.alter_balance -= price

            if user.alter_balance < 0:
                await session.rollback()
                return {
                    "message": "У вас недостаточно средств",
                }

            stmt = select(Wife).where(Wife.id == wife_id)
            result = await session.execute(stmt)
            wife = result.scalar_one_or_none()

            if wife is None:
                return {
                    "message": "Такого персонажа нет",
                }

            user.characters.append(wife)

            await session.commit()
            return {
                "message": "Покупка удалась"
            }

        except Exception as e:
            return {
                "error": str(e),
                "message": "У вас уже есть эта вайфа",
            }
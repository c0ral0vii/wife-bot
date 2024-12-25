
from sqlalchemy import select
from src.database.models import Promo
from src.database.database import async_session


async def add_promo(promocode: str, bonus: int):
    async with async_session() as session:
        promo = Promo(
            bonus=float(bonus),
            promo=promocode,
        )

        session.add(promo)
        await session.commit()
        return {
            "message": "Промокод успешно добавлен",
        }
        
async def get_promo(promocode: str = None, admin : bool = False):
    async with async_session() as session:
        stmt = select(Promo).where(Promo.promo == promocode)
        result = await session.execute(stmt)
        promo = result.scalar_one_or_none()

        if not promo:
            return
        if admin:
            return result.scalars().all()

        return promo.bonus

async def delete_promo(promocode: str):
    async with async_session() as session:
        stmt = select(Promo).where(Promo.promo == promocode)
        result = await session.execute(stmt)
        promo = result.scalar_one_or_none()

        if not promo:
            return {
                "message": "Промокод не найден",
            }

        await session.delete(promo)
        await session.commit()
        return {
            "message": "Промокод удален"
        }


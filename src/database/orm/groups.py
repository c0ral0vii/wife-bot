from sqlalchemy import select, or_, func

from src.database.database import async_session
from src.database.models import ProductGroups


async def get_groups():
    async with async_session() as session:
        stmt = select(ProductGroups)
        result = await session.execute(stmt)
        groups = result.scalars().all()

        return groups


async def create_group(chat_id: int, join_link: str):
    async with async_session() as session:
        try:
            new_group = ProductGroups(
                group_link=join_link,
                chat_id=chat_id,
            )

            session.add(new_group)
            await session.commit()

            return {
                "message": "Группа создана",
            }
        except Exception as e:
            return {
                "error": str(e),
                "message": "Ошибка, такая группа уже существует"
            }


async def delete_group_db(join_link: str = None):
    async with async_session() as session:
        stmt = select(ProductGroups).where(
            ProductGroups.group_link == join_link,
        )
        result = await session.execute(stmt)
        group = result.scalars().first()

        if not group:
            return {
                "message": "Группа не найдена"
            }

        await session.delete(group)
        await session.commit()

        return {
            "message": "Группа успешно удалена",
        }


async def get_random_group():
    async with async_session() as session:
        # Use func.random() to get a random group
        stmt = select(ProductGroups).order_by(func.random()).limit(1)
        result = await session.execute(stmt)
        random_group = result.scalars().first()

        if not random_group:
            return {
                "message": "Группы не найдены"
            }

        return random_group


async def get_group(group_id: int):
    async with async_session() as session:
        stmt = select(ProductGroups).where(ProductGroups.id == group_id)
        result = await session.execute(stmt)
        group = result.scalar_one_or_none()
        if not group:
            return {
                "message": "Такой группы больше нет =("
            }

        return {
            "data": group,
            "message": f"🎉Вы получили бонус 💠{group.bonus}"
        }
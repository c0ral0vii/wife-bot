from sqlalchemy import select
from src.database.models import AdminUser
from src.database.database import async_session


async def get_admins():
    async with async_session() as session:
        stmt = select(AdminUser)
        result = await session.execute(stmt)
        admins = result.scalars().all()

        return admins
    

async def add_admin(user_id: str):
    async with async_session() as session:
        try:
            new_admin = AdminUser(
                user_id=int(user_id),
            )

            session.add(new_admin)
            await session.commit()
            return {
                "message": "Админ добавлен"
            }
        except:
            return {
                "message": "Возможно этот админ уже в базе или вы не правильно ввели формат"
            }


async def remove_admin(user_id: str):
    async with async_session() as session:
        try:
            stmt = select(AdminUser).where(AdminUser.user_id == int(user_id))
            result = await session.execute(stmt)
            admin = result.scalar_one_or_none()

            if admin is None:
                return {
                    "message": "Возможно такого админа нет"
                }

            await session.delete(admin)
            await session.commit()
            return {
                "message": "Админ успешно удален"
            }
        except:
            return {
                "message": "Возможно этот админ уже в базе или вы не правильно ввели формат"
            }
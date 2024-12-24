from src.database.models import BannedUser
from sqlalchemy import select
from src.database.database import async_session


async def get_blocks():
    async with async_session() as session:
        stmt = select(BannedUser)
        result = await session.execute(stmt)
        admins = result.scalars().all()

        return admins


async def add_block(user_id: str):
    async with async_session() as session:
        try:
            new_admin = BannedUser(
                user_id=int(user_id),
            )

            session.add(new_admin)
            await session.commit()
            return {
                "message": "Пользователь заблокирован"
            }
        except:
            return {
                "message": "Возможно этот пользователь уже заблокирован или вы не правильно ввели формат"
            }


async def remove_block(user_id: str):
    async with async_session() as session:
        try:
            stmt = select(BannedUser).where(BannedUser.user_id == int(user_id))
            result = await session.execute(stmt)
            admin = result.scalar_one_or_none()

            if admin is None:
                return {
                    "message": "Возможно такого заблокированого пользователя нет"
                }

            await session.delete(admin)
            await session.commit()
            return {
                "message": "Заблокированый пользователь успешно удален"
            }
        except:
            return {
                "message": "Возможно этот заблокированый пользователь уже в базе или вы не правильно ввели формат"
            }
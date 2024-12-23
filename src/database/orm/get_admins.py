from sqlalchemy import select
from src.database.models import AdminUser
from src.database.database import async_session


async def get_admins():
    async with async_session() as session:
        stmt = select(AdminUser)
        result = await session.execute(stmt)
        admins = result.scalars().all()

        return admins
    

async def add_admin(user_id: int):
    async with async_session() as session:
        new_admin = AdminUser(
            user_id=int(user_id),
        )

        session.add(new_admin)
        await session.commit()
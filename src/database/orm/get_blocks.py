from src.database.models import BannedUser
from sqlalchemy import select
from src.database.database import async_session


async def get_blocks():
    async with async_session() as session:
        stmt = select(BannedUser)
        result = await session.execute(stmt)
        admins = result.scalars().all()

        return admins
from src.database.database import async_session
from src.database.models import Wife, User, Trade
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def answer_trade(user_id: int, sender_user_id: int):
    async with async_session() as session:
        sender_stmt = select(User).where(User.user_id == sender_user_id)
        
        
        user_stmt = select(User).where(User.user_id == user_id)

        
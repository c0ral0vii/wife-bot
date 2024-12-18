from src.database.models import Wife, User
from src.database.database import async_session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload


async def get_character(id: int):
    async with async_session() as session:
        stmt = select(Wife).where(Wife.id == id)
        result = await session.execute(stmt)
        wife = result.scalar_one_or_none()

        if not wife:
            return wife
        
        return wife


async def remove_wife_from_user(user_id: int, wife_id: int, session):
    try:
        # Fetch the user and wife objects with eager loading
        user_stmt = select(User).options(joinedload(User.characters)).where(User.user_id == user_id)
        wife_stmt = select(Wife).where(Wife.id == wife_id)
        
        user_result = await session.execute(user_stmt)
        wife_result = await session.execute(wife_stmt)
        
        user = user_result.unique().scalars().one_or_none()
        wife = wife_result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User with user_id {user_id} not found.")
        
        if not wife:
            raise ValueError(f"Wife with id {wife_id} not found.")
        
        # Check if the wife is in the user's characters and remove it
        if wife in user.characters:
            user.characters.remove(wife)
            await session.commit()
            return {"status": "success", "message": "Wife removed from user's characters."}
        else:
            return {"status": "warning", "message": "Wife not found in user's characters."}
    
    except SQLAlchemyError as e:
        await session.rollback()
        raise e  # or handle the exception as needed
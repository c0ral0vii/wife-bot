from src.database.models import Wife, User, AllRares
from src.database.database import async_session
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
import random
import datetime
from src.redis.services import redis_manager


async def get_character(id: int):
    async with async_session() as session:
        stmt = select(Wife).where(Wife.id == id)
        result = await session.execute(stmt)
        wife = result.scalar_one_or_none()

        if not wife:
            return wife
        
        return wife
    

async def add_random_wifes_to_redis(user_id: int, refresh: bool = False):
    """
    Добавляет случайные вайфы в Redis для текущей даты.
    """
    async with async_session() as session:
        # Получаем текущую дату в формате YYYY-MM-DD
        redis_client = await redis_manager.get_redis()
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        redis_key = f"shop:{current_date}:{user_id}"

        # Проверяем, есть ли уже данные для текущей даты
        if refresh:
            await redis_client.delete(redis_key)
        if await redis_client.exists(redis_key):
            return  # Данные уже добавлены

        # Список редкостей для выбора
        rarities = [AllRares.SIMPLE, AllRares.RARE, AllRares.EPIC, AllRares.LEGENDARY]

        # Выбираем по одному случайному вайфу для каждой редкости
        for rarity in rarities:
            query = select(Wife).where(Wife.rare == rarity)
            result = await session.execute(query)
            wifes = result.scalars().all()

            if wifes:
                random_wife = random.choice(wifes)
                await redis_client.hset(redis_key, rarity, random_wife.id)

        print(f"Добавлены случайные вайфы в Redis для ключа {redis_key}")


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
    

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from src.database.models import Wife, User
from src.database.database import async_session


async def my_wifes(user_id: int) -> list:
    async with async_session() as sesssion:
        stmt = select(User).options(joinedload(User.characters)).where(User.user_id == user_id)
        result = await sesssion.execute(stmt)
        user = result.unique().scalar_one_or_none()

        if not user:
            return
        
        return user.characters
    

async def add_wife(data: dict):
    async with async_session() as session:
        wife = Wife(
            name=data.get("title"),
            rare=data.get("rarity"),
            from_=','.join(data.get("anime_list")),
            wife_imgs=data.get("img")
        )

        session.add(wife)
        await session.commit()
        return wife
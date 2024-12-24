from typing import Dict, Any, NoReturn, Union
from sqlalchemy import select, func
from sqlalchemy.orm import aliased, joinedload, selectinload
from decimal import Decimal

from src.database.database import async_session
from src.database.models import User, UserStatus, Wife, user_wife_association, AllRares

async def create_user(data: Dict[str, Any]) -> Dict:
    try:
        async with async_session() as session:
            stmt = select(User).options(selectinload(User.characters)).where(User.user_id == data.get("user_id"))
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if user:
                return {
                    "create": False,
                    "id": user.id,
                    "data": user,
                    "user_id": data.get("user_id"),
                    "text": "Существует"
                }

            user = User(
                user_id=data.get("user_id"),
                username=data.get("username", "Не задано"),
                profile_imgs="./media/profiles/default/",
            )
            session.add(user)
            await session.commit()

            return {
                "create": True,
                "id": user.id,
                "data": user,
                "user_id": data.get("user_id"),
                "text": "Создан"
            }
    except Exception as e:
        print(e)
        await session.rollback()


async def check_vip(data: Dict[str, Any]) -> Dict:
    async with async_session() as session:
        stmt = select(User).where(User.user_id == data.get("user_id"))
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            return {
                "bool_": False,
                "text": "Не вип",
            }
        
        if user.status == UserStatus.NOT_VIP:
            return {
                "status": user.status,
                "bool_": False,
                "text": "Не вип",
            }
        
        return {
            "status": user.status,
            "bool_": True,
            "text": user.status.value,
        }
    

async def get_user(user_id: int = None, username: str = None) -> User | NoReturn:
    async with async_session() as session:
        if username:
            stmt = select(User).where(User.username == username)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()

            if not user:
                return
            return user
            
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return
        
        return user
    




async def get_count_wifes(user: User) -> Dict[str, Union[int, Dict[str, int]]]:
    user_counts = {
        "my_simple": 0,
        "my_rare": 0,
        "my_epic": 0,
        "my_legendary": 0
    }
    total_counts = {
        "total_simple": 0,
        "total_rare": 0,
        "total_epic": 0,
        "total_legendary": 0
    }
    percentages = {
        "my_total_percent": 0,
        "my_simple_percent": 0,
        "my_rare_percent": 0,
        "my_epic_percent": 0,
        "my_legendary_percent": 0
    }
    async with async_session() as session:
        # Query for user's counts per rarity
        user_character_alias = aliased(user_wife_association)
        character_alias = aliased(Wife)
        
        query_user_rarities = await session.execute(
            select(
                character_alias.rare,
                func.count(func.distinct(character_alias.id)).label("count")
            )
            .select_from(user_character_alias)
            .join(character_alias, user_character_alias.c.wife_id == character_alias.id)
            .where(user_character_alias.c.user_id == user.id)
            .group_by(character_alias.rare)
        )
        total_count = 0
        # Update user_counts based on query results
        for rarity, count in query_user_rarities.fetchall():
            total_count += count
            if rarity == AllRares.SIMPLE:
                user_counts["my_simple"] = count
            elif rarity == AllRares.RARE:
                user_counts["my_rare"] = count
            elif rarity == AllRares.EPIC:
                user_counts["my_epic"] = count
            elif rarity == AllRares.LEGENDARY:
                user_counts["my_legendary"] = count
        
        # Query for total counts per rarity across all users
        query_total_rarities = await session.execute(
            select(
                character_alias.rare,
                func.count(func.distinct(character_alias.id)).label("count")
            )
            .select_from(character_alias)
            .group_by(character_alias.rare)
        )
        
        # Update total_counts based on query results
        for rarity, count in query_total_rarities.fetchall():
            if rarity == AllRares.SIMPLE:
                total_counts["total_simple"] = count
            elif rarity == AllRares.RARE:
                total_counts["total_rare"] = count
            elif rarity == AllRares.EPIC:
                total_counts["total_epic"] = count
            elif rarity == AllRares.LEGENDARY:
                total_counts["total_legendary"] = count
        
        # Query for total number of unique characters across all users
        query_total_characters = await session.execute(
            select(func.count(func.distinct(character_alias.id)))
            .select_from(character_alias)
        )
        
        # Get the total count
        total_characters = query_total_characters.scalar_one_or_none() or 0
        if total_characters > 0:
            percentages["my_total_percent"] = (total_count / total_characters) * 100
            percentages["my_simple_percent"] = (user_counts["my_simple"] / total_counts["total_simple"]) * 100
            percentages["my_rare_percent"] = (user_counts["my_rare"] / total_counts["total_rare"]) * 100
            percentages["my_epic_percent"] = (user_counts["my_epic"] / total_counts["total_epic"]) * 100
            percentages["my_legendary_percent"] = (user_counts["my_legendary"] / total_counts["total_legendary"]) * 100

        # Prepare the result dictionary
        result = {
            "my_total": total_count,
            "total_counts": total_characters,
            **total_counts,
            **user_counts,
            **percentages,
        }
        
        return result


async def change_nickname(user_id: int, new_username: str) -> bool:
    async with async_session() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            return
        
        user.username = new_username
        session.add(user)
        await session.commit()


async def add_balance(user_id: int, add_to: Decimal | int | float):
    async with async_session() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        procent = None
        if user.status == UserStatus.BASE_VIP:
            procent = 120
        if user.status == UserStatus.MIDDLE_VIP:
            procent = 130
        if user.status == UserStatus.SUPER_VIP:
            procent = 150
        
        if procent:
            add_to = Decimal(add_to) * (Decimal(procent) / 100)

        user.balance = Decimal(f"{user.balance}") + Decimal(add_to)

        session.add(user)
        await session.commit()

        return {
            "value": add_to,
            "balance": user.balance
        }
    

async def add_alter_balance(user_id: int, add_to: Decimal | int | float):
    async with async_session() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()
        procent = None
        if user.status == UserStatus.BASE_VIP:
            procent = 120
        if user.status == UserStatus.MIDDLE_VIP:
            procent = 130
        if user.status == UserStatus.SUPER_VIP:
            procent = 150
        
        if procent:
            add_to = Decimal(add_to) * (Decimal(procent) / 100)

        user.alter_balance = Decimal(f"{user.alter_balance}") + Decimal(add_to)

        session.add(user)
        await session.commit()

        return {
            "value": add_to,
            "balance": user.balance
        }
    

async def remove_balance(user_id: int, amount_to_remove: int | float | Decimal):
    """
    Уменьшает баланс пользователя на указанную сумму, но не ниже 0.
    """
    async with async_session() as session:
        # Находим пользователя
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"Пользователь с user_id {user_id} не найден.")

        # Преобразуем баланс в Decimal для точных вычислений
        current_balance = Decimal(f"{user.balance}")

        # Вычисляем новый баланс
        new_balance = current_balance - Decimal(amount_to_remove)

        # Убеждаемся, что баланс не становится отрицательным
        if new_balance < Decimal("0.00"):
            new_balance = Decimal("0.00")
            return False

        # Обновляем баланс пользователя
        user.balance = new_balance

        # Сохраняем изменения в базе данных
        session.add(user)
        await session.commit()

        return new_balance


async def get_top_users_by_characters(limit: int = 10):
    """
    Получает топ пользователей по количеству персонажей.
    """
    async with async_session() as session:
        query = (
            select(User.username, func.count(user_wife_association.c.wife_id).label("characters_count"))
            .join(user_wife_association, User.id == user_wife_association.c.user_id)
            .group_by(User.id)
            .order_by(func.count(user_wife_association.c.wife_id).desc())
            .limit(limit)
        )
        result = await session.execute(query)
        users = result.fetchall()
        return users 
    

async def get_top_users_by_legendary(limit: int = 10):
    """
    Получает топ пользователей по количеству легендарных персонажей.
    """
    async with async_session() as session:
        query = (
            select(User.username, func.count(Wife.id).label("legendary_count"))
            .join(user_wife_association, User.id == user_wife_association.c.user_id)
            .join(Wife, user_wife_association.c.wife_id == Wife.id)
            .where(Wife.rare == AllRares.LEGENDARY)
            .group_by(User.id)
            .order_by(func.count(Wife.id).desc())
            .limit(limit)
        )
        result = await session.execute(query)
        users = result.fetchall()
        return users
    
    
async def check_user_has_wife(wife_id: int, user_id: int):
    async with async_session() as session:
        query = (
            select(User)
            .join(User.characters)
            .where(User.user_id == user_id)
            .where(Wife.id == wife_id)
        )

        result = await session.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            return
        return user
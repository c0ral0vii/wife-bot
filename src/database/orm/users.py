from typing import Dict, Any, NoReturn
from sqlalchemy import select, func
from sqlalchemy.orm import aliased, joinedload
from decimal import Decimal

from src.database.database import async_session
from src.database.models import User, UserStatus, Wife, user_wife_association, AllRares


async def create_user(data: Dict[str, Any]) -> Dict:
    try:
        async with async_session() as session:
            async with async_session() as session:
                stmt = select(User).where(User.user_id == data.get("user_id"))
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
    



async def get_count_wifes(user: User) -> Dict[str, int]:
    async with async_session() as session:
        user_wife_alias = aliased(user_wife_association)

        # Explicitly specify select_from and the ON condition for the join
        query = await session.execute(
            select(
                func.count(user_wife_alias.c.wife_id).label("total_wifes")
            )
            .select_from(user_wife_alias)  # Set the left side explicitly
            .join(User, User.id == user_wife_alias.c.user_id)  # Define the ON clause
            .where(User.id == user.id)
        )

        # Extract the result
        total_wifes = query.scalar_one_or_none()  # Use scalar_one_or_none for better safety
        return {"total_wifes": total_wifes or 0}  # Handle None case


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
            "value": add_to
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
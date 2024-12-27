from datetime import date, timedelta
from sqlalchemy import select
from src.database.database import async_session
from src.database.models import User, UserStatus


async def set_vip_status(user_id: int, vip_status: UserStatus):
    """
    Устанавливает уровень VIP для пользователя и автоматически добавляет срок действия на 1 месяц.

    :param session: Асинхронная сессия SQLAlchemy.
    :param user_id: ID пользователя, для которого устанавливается VIP статус.
    :param vip_status: Уровень VIP (из перечисления UserStatus).
    """
    # Находим пользователя по user_id
    async with async_session() as session:
        stmt = select(User).where(User.user_id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise ValueError(f"Пользователь с ID {user_id} не найден.")

        # Устанавливаем новый статус
        user.status = vip_status

        # Если статус VIP (не "Обычный пользователь"), устанавливаем срок действия на 1 месяц
        if vip_status != UserStatus.NOT_VIP:
            user.vip_to = date.today() + timedelta(days=30)
        else:
            # Если статус "Обычный пользователь", сбрасываем срок действия
            user.vip_to = None

        session.add(user)
        await session.commit()
from src.database.database import async_session
from src.database.models import Wife, User, Trade
from sqlalchemy import select
from sqlalchemy.orm import selectinload


async def send_trade(from_user_id: int, to_user_id: int, wife_id: int):
    """
    Отправляет трейд от одного пользователя к другому.
    """
    async with async_session() as session:
        # Получаем отправителя
        from_user = await session.execute(select(User).options(selectinload(User.characters)).where(User.user_id == from_user_id))
        from_user = from_user.unique().scalar_one_or_none()
        if not from_user:
            raise ValueError("Отправитель не найден.")

        # Получаем получателя
        to_user = await session.execute(select(User).where(User.user_id == to_user_id))
        to_user = to_user.scalar_one_or_none()
        if not to_user:
            raise ValueError("Получатель не найден.")

        # Получаем вайфу
        wife = await session.execute(select(Wife).where(Wife.id == wife_id))
        wife = wife.scalar_one_or_none()
        if not wife:
            raise ValueError("Вайфа не найдена.")

        # Создаем новый трейд
        trade = Trade(
            from_id=from_user.id,
            to_id=to_user.id,
            change_from_id=wife.id,
            change_to_id=None,
            sucess=False
        )
        from_user.characters.remove(wife)  # Убираем вайфу у отправителя
        session.add(trade)
        await session.commit()

        return trade
    

async def cancel_trade(trade_id: int):
    """
    Отменяет трейд и возвращает вайфу отправителю.
    """
    # Получаем трейд
    async with async_session() as session: 
        trade = await session.execute(select(Trade).options(
                selectinload(Trade.to_).selectinload(User.characters),
                selectinload(Trade.from_),
                selectinload(Trade.change_from),
                selectinload(Trade.change_to)
            ).where(Trade.id == trade_id))
        trade = trade.scalar_one_or_none()
        if not trade:
            raise ValueError("Трейд не найден.")

        # Получаем пользователя и вайфу
        from_user = await session.execute(select(User).options(selectinload(User.characters)).where(User.id == trade.from_id))
        from_user = from_user.scalar_one_or_none()
        if not from_user:
            raise ValueError("Отправитель не найден.")

        wife = await session.execute(select(Wife).where(Wife.id == trade.change_from_id))
        wife = wife.scalar_one_or_none()
        if not wife:
            raise ValueError("Вайфа не найдена.")

        # Возвращаем вайфу отправителю
        from_user.characters.append(wife)

        if trade.change_to_id:
            wife = await session.execute(select(Wife).where(Wife.id == trade.change_to_id))
            wife = wife.scalar_one_or_none()
            if not wife:
                raise ValueError("Вайфа не найдена.")
            
            from_user = await session.execute(select(User).options(selectinload(User.characters)).where(User.id == trade.to_id))
            from_user = from_user.scalar_one_or_none()
            if not from_user:
                raise ValueError("Отправитель не найден.")
            trade.to_.characters.append(wife)

        await session.delete(trade)  # Удаляем трейд
        await session.commit()

        return trade


async def accept_trade_with_exchange(trade_id: int, exchange_wife_id: int):
    """
    Принимает трейд и добавляет вайфу в обмен.
    """
    async with async_session() as session:
        # Получаем трейд с загрузкой связанных объектов
        trade = await session.execute(
            select(Trade)
            .options(
                selectinload(Trade.to_).selectinload(User.characters),
                selectinload(Trade.from_),
                selectinload(Trade.change_from),
                selectinload(Trade.change_to)
            )
            .where(Trade.id == trade_id)
        )
        trade = trade.scalar_one_or_none()
        if not trade:
            raise ValueError("Трейд не найден.")

        # Получаем вайфу для обмена
        exchange_wife = await session.execute(select(Wife).where(Wife.id == exchange_wife_id))
        exchange_wife = exchange_wife.scalar_one_or_none()
        if not exchange_wife:
            raise ValueError("Вайфа для обмена не найдена.")

        # Проверяем, что вайфа для обмена принадлежит пользователю, который принимает трейд
        if exchange_wife not in trade.to_.characters:
            raise ValueError("Эта вайфа не принадлежит вам.")

        # Обновляем трейд, добавляем `change_to_id`
        trade.change_to_id = exchange_wife_id
        trade.sucess = False

        trade.to_.characters.remove(exchange_wife)

        await session.commit()

        return trade
    

async def final_accept_trade_with_exchange(trade_id: int):
    """
    Принимает трейд и добавляет вайфу в обмен.
    """
    async with async_session() as session:
        # Получаем трейд с загрузкой связанных объектов
        trade = await session.execute(
            select(Trade)
            .options(
                selectinload(Trade.to_).selectinload(User.characters),
                selectinload(Trade.from_).selectinload(User.characters),
                selectinload(Trade.change_from),
                selectinload(Trade.change_to)
            )
            .where(Trade.id == trade_id)
        )
        trade = trade.scalar_one_or_none()
        if not trade:
            raise ValueError("Трейд не найден.")

        # Получаем вайфу для обмена
        exchange_wife = await session.execute(select(Wife).where(Wife.id == trade.change_to_id))
        exchange_wife = exchange_wife.scalar_one_or_none()
        if not exchange_wife:
            raise ValueError("Вайфа для обмена не найдена.")
        to_wife = await session.execute(select(Wife).where(Wife.id == trade.change_from_id))
        to_wife = to_wife.scalar_one_or_none()
        if not to_wife:
            raise ValueError("Вайфа для обмена не найдена.")
        # Проверяем, что вайфа для обмена принадлежит пользователю, который принимает трейд
        if exchange_wife in trade.to_.characters:
            raise ValueError("Эта вайфа у вас есть")

        # Обновляем трейд, добавляем `change_to_id`
        trade.sucess = True

        # Удаляем вайфу из списка персонажей пользователя, который принимает трейд
        trade.from_.characters.append(exchange_wife)

        # Добавляем вайфу к пользователю, который отправляет трейд
        trade.to_.characters.append(to_wife)

        await session.commit()

        return trade
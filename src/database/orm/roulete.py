import random
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from src.database.models import User, Wife, AllRares, Sex, UserStatus
from src.database.database import async_session  # Предполагается, что у вас есть фабрика сессий


async def spin_character(user_id: int, rarity: AllRares = None, sex: Sex = None) -> Wife:
    """
    Прокрутка персонажа с учетом редкости.
    Если редкость не указана, то выбирается случайная редкость с учетом процентов.
    Пользователь не может получить вайфу, которая уже есть у него.
    """

    SPIN_PROBABILITIES = {
        AllRares.SIMPLE: 57,
        AllRares.RARE: 23,
        AllRares.EPIC: 15,
        AllRares.LEGENDARY: 5,
    }

    async with async_session() as session:
        # Находим пользователя и его коллекцию вайф
        user_query = select(User).where(User.user_id == user_id).options(selectinload(User.characters))
        result = await session.execute(user_query)
        user = result.scalars().first()

        if user.status == UserStatus.BASE_VIP:
            SPIN_PROBABILITIES = {
                AllRares.SIMPLE: 49,
                AllRares.RARE: 23,
                AllRares.EPIC: 20,
                AllRares.LEGENDARY: 8,
            }
        if user.status == UserStatus.MIDDLE_VIP:
            SPIN_PROBABILITIES = {
                AllRares.SIMPLE: 42,
                AllRares.RARE: 23,
                AllRares.EPIC: 25,
                AllRares.LEGENDARY: 10,
            }
        if user.status == UserStatus.SUPER_VIP:
            SPIN_PROBABILITIES = {
                AllRares.SIMPLE: 25,
                AllRares.RARE: 23,
                AllRares.EPIC: 35,
                AllRares.LEGENDARY: 17,
            }

        if not user:
            raise ValueError(f"Пользователь с user_id {user_id} не найден.")

        # Получаем список ID вайф, которые уже есть у пользователя
        user_wife_ids = {wife.id for wife in user.characters}

        # Выбираем редкость с учетом процентов, если она не указана
        if rarity is None:
            rarity = random.choices(
                list(SPIN_PROBABILITIES.keys()),
                weights=SPIN_PROBABILITIES.values(),
                k=1
            )[0]

        # Получаем всех персонажей с выбранной редкостью, которых нет у пользователя
        if sex is None:
            query = select(Wife).where(
                Wife.rare == rarity,
                Wife.id.notin_(user_wife_ids)  # Исключаем вайфы, которые уже есть у пользователя
            )
        else:
            query = select(Wife).where(
                and_(
                    Wife.rare == rarity,
                    Wife.sex == sex,
                ),
                Wife.id.notin_(user_wife_ids)  # Исключаем вайфы, которые уже есть у пользователя
            )

        result = await session.execute(query)
        characters = result.scalars().all()

        if not characters:
            raise ValueError(f"Для вас персонажей этой редкости нет -> {rarity.value}.")

        # Выбираем случайный персонаж из списка
        win_character = random.choice(characters)

        # Добавляем выигранного персонажа в коллекцию пользователя
        user.characters.append(win_character)

        # Сохраняем изменения в базе данных
        await session.commit()

        return win_character
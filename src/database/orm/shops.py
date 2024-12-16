from sqlalchemy import select, delete
from src.database.models import Shop, ShopTypes
from src.database.database import async_session
from src.logger import setup_logger

logger = setup_logger(__name__)


async def create_local_shop(chat_id: int, type: ShopTypes) -> Shop:
    async with async_session() as session:
        try:
            stmt = select(Shop).where(Shop.chat_id == chat_id)
            result = await session.execute(stmt)
            shop = result.scalar_one_or_none()

            if shop:
                return shop
            
            shop = Shop(
                chat_id = chat_id,
                type = type,
            )

            session.add(shop)
            await session.commit()

            return shop
        except Exception as e:
            logger.warning(f"Не удалось создать локальный рынок - {chat_id}")
            await session.rollback()
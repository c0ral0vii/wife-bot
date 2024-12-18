from sqlalchemy import select, delete, and_
from src.database.models import Shop, ShopTypes, Slot, User, Wife
from sqlalchemy.orm import selectinload
from src.database.database import async_session
from decimal import Decimal
from src.logger import setup_logger
from src.database.orm.users import create_user
from src.database.orm.wifes import get_character, remove_wife_from_user
from sqlalchemy.orm import joinedload, lazyload

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


async def create_slot(user_id: int, wife_id: int, price: float | int, shop_id: int) -> Slot:
    async with async_session() as session:
        try:
            await remove_wife_from_user(user_id=user_id, wife_id=wife_id, session=session)
            slot = Slot(
                price=Decimal(price),
                closed=False,
                selled=False,
                wife_id=wife_id,
                shop_id=shop_id,
                seller_id=user_id
            )

            session.add(slot)
            await session.commit()
            return slot
        except Exception as e:
            logger.error(f"Failed to create slot: {e}")
            await session.rollback()
            return None
        

async def get_wifes_for_user(user_id: int) -> list[Wife]:
    async with async_session() as session:
        try:
            # Construct the query to select the User and eager load the characters relationship
            stmt = select(User).options(selectinload(User.characters)).where(User.user_id == user_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            
            if user:
                # Return the list of Wife objects associated with the user
                return user.characters
            else:
                # User not found
                return []
        except Exception as e:
            # Handle exceptions, e.g., log the error
            logger.error(f"Error retrieving wifes for user {user_id}: {e}")
            return []



async def get_all_slots_from_shop(chat_id: int) -> list[Slot]:    
    async with async_session() as session:
        # Fetch the shop with its slots eagerly loaded
        stmt = select(Shop).options(joinedload(Shop.slots).joinedload(Slot.wife)).where(Shop.chat_id == chat_id)
        result = await session.execute(stmt)
        shop = result.unique().scalar_one_or_none()
        
        if shop:
            return shop.slots
        else:
            return []
    
    
async def get_wife_from_slot(slot_id: int) -> Wife:
    async with async_session() as session:
        stmt = select(Slot).options(joinedload(Slot.wife)).where(Slot.id == slot_id)
        result = await session.execute(stmt)
        slot = result.unique().scalar_one_or_none()

        if slot:
            return slot.wife
        else:
            return
        

async def get_slot(id: int):
    async with async_session() as session:
        stmt = select(Slot).where(Slot.id == id)
        result = await session.execute(stmt)
        slot = result.scalar_one_or_none()

        if slot:
            return slot
        return None


async def get_my_slots(user_id: int):
    async with async_session() as session:
        stmt = select(Slot).options(
            joinedload(Slot.wife),
        ).where(Slot.seller_id == user_id)

        result = await session.execute(stmt)
        slots = result.unique().scalars().all()

        if slots:
            return slots 


async def cancel_slot(slot_id: int, seller_user_id: int) -> dict:
    try:
        async with async_session() as session:
            # Fetch the slot with associated wife and shop
            stmt = select(Slot).options(
                joinedload(Slot.wife),
                joinedload(Slot.seller).joinedload(User.characters)
            ).where(Slot.id == slot_id)
            result = await session.execute(stmt)
            slot = result.unique().scalar_one_or_none()
            
            if not slot:
                return {"status": "error", "message": "Slot not found."}
            
            if slot.closed or slot.selled:
                return {"status": "error", "message": "Slot is already closed or sold and cannot be canceled."}
            
            # Ensure the seller_user_id matches the slot's seller_id
            if slot.seller_id != seller_user_id:
                return {"status": "error", "message": "Seller does not own this slot."}
            
            # Remove wife from seller's characters
            seller = slot.seller
            if slot.wife not in seller.characters:
                seller.characters.append(slot.wife)
            else:
                return {
                    "status": "error",
                    "message": "Не получено"
                }
            
            # Delete the slot
            await session.delete(slot)
            await session.commit()
            return {"status": "success", "message": "Slot canceled successfully."}
    
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to cancel slot {slot_id}: {e}")
        return {"status": "error", "message": "An error occurred during cancellation."}
    

async def purchase_slot(slot_id: int, buyer_user_id: int) -> dict:
    async with async_session() as session:
        try:
            # Fetch the slot with associated wife and shop
            stmt = select(Slot).options(
                joinedload(Slot.wife),
                joinedload(Slot.seller),
            ).where(Slot.id == slot_id)
            result = await session.execute(stmt)
            slot = result.scalar_one_or_none()

            if not slot:
                return {"status": "error", "message": "Slot not found."}
            
            if slot.closed or slot.selled:
                return {"status": "error", "message": "Slot is already closed or sold."}
            
            # Fetch the buyer user
            buyer_stmt = select(User).options(joinedload(User.characters)).where(User.user_id == buyer_user_id)
            buyer_result = await session.execute(buyer_stmt)
            buyer = buyer_result.unique().scalar_one_or_none()

            if not buyer:
                return {"status": "error", "message": "Buyer user not found."}
            
            # Check if buyer has enough balance
            if buyer.balance < slot.price:
                return {"status": "error", "message": "Insufficient balance."}
            
            if buyer.user_id == slot.seller.user_id:
                return {"status": "error", "message": "Cannot buy your own slot."}

            # Update balances and ownership
            buyer.balance -= slot.price
            slot.seller.balance += slot.price
            buyer.characters.append(slot.wife)
            slot.selled = True
            slot.closed = False

            session.add_all([slot, buyer])

            await session.commit()

            return {"status": "success", "message": "Slot purchased successfully."}
        except Exception as e:
            logger.error(f"Failed to purchase slot {slot_id}: {e}")
            await session.rollback()  # Откат изменений
            return {"status": "error", "message": str(e)}

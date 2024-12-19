from src.database.models import Wife
from src.database.database import async_session
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload


async def find_characters(text: str):
    if not text:
        return 
    
    search_pattern = f'%{text}%'
    
    async with async_session() as session:
        stmt = select(Wife).where(or_(
            Wife.from_.ilike(search_pattern),
            Wife.name.ilike(search_pattern),
            Wife.id.ilike(search_pattern),
        ))
        
        result = await session.execute(stmt)
        wives = result.scalars().first()
        
        if not wives:
            return 
        
        return wives
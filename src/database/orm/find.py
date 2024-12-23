from src.database.models import Wife
from src.database.database import async_session
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload


async def find_characters(text: str, from_title: str = False):
    if not text:
        return 
    
    search_pattern = f'%{text}%'
    
    async with async_session() as session:
        stmt = select(Wife).where(or_(
            Wife.name.ilike(search_pattern),
        ))
        if from_title:
            stmt = select(Wife).where(or_(
                Wife.from_.ilike(search_pattern)
            ))

        result = await session.execute(stmt)
        wifes = result.scalars().all()
        
        if not wifes:
            return 
        
        return wifes
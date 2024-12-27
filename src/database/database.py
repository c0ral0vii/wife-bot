from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.config.config import settings


_DATABASE_URL = settings.database_link

print(_DATABASE_URL)
engine = create_async_engine(
    _DATABASE_URL,
    echo=settings.get_debug_settings,
    # poll_size=10,
    max_overflow=20,
)


async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
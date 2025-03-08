from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from config import get_config

config = get_config()
DB_URI = config.SQLALCHEMY_DATABASE_URI
if DB_URI.startswith('sqlite'):
    ASYNC_DB_URI = DB_URI.replace('sqlite', 'sqlite+aiosqlite', 1)
else:
    ASYNC_DB_URI = DB_URI.replace('postgresql', 'postgresql+asyncpg', 1)

async_engine = create_async_engine(ASYNC_DB_URI, echo=config.DEBUG)
AsyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=async_engine,
    class_=AsyncSession
)
Base = declarative_base()

async def get_async_db():
    async_session = AsyncSessionLocal()
    try:
        yield async_session
    finally:
        await async_session.close()

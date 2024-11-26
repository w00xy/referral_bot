from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from config import DB_LITE
from database.models import Base

engine = create_async_engine(DB_LITE, echo=True)

session_maker = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


# @DeprecationWarning
async def create_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
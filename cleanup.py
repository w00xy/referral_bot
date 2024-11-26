import asyncio
from database.models import ChannelRequests
from database.engine import session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func

from config import DB_LITE

async def cleanup_duplicate_requests(session: AsyncSession):
    # Find duplicate rows based on user_id and channel_id
    duplicate_requests = await session.execute(
        select(ChannelRequests).group_by(ChannelRequests.user_id, ChannelRequests.channel_id).having(func.count() > 1)
    )
    duplicate_requests = duplicate_requests.scalars().all()

    # Delete all but the first occurrence of each duplicate.  We keep the one with lowest ID for simplicity
    for req in duplicate_requests:
        await session.execute(
            delete(ChannelRequests).where(
                ChannelRequests.user_id == req.user_id,
                ChannelRequests.channel_id == req.channel_id,
                ChannelRequests.id != req.id
            )
        )
    await session.commit()
    
async def clean_up():
    # Call this function once to fix your database:
    async with session_maker() as session:
        await cleanup_duplicate_requests(session)
        
if __name__ == "__main__":
    asyncio.run(clean_up())
    

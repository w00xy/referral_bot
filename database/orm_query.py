from aiogram.loggers import event
from sqlalchemy import select, update, delete, values, desc
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.exc import SQLAlchemyError, MultipleResultsFound, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlalchemy.util.langhelpers import repr_tuple_names

from config import MONEY_AMOUNT
from database.engine import session_maker
from database.models import User, Referral, Channel, ChannelRequests, UserHistory, HelpMessage


async def orm_get_user(session: AsyncSession, user_id: int) -> User:
    query = select(User).where(User.user_id == user_id)

    user = await session.execute(query)

    # Use fetchone() to get the first result
    user = user.scalar_one_or_none()

    return user



async def orm_add_user(
    session: AsyncSession,
    user_id: int,
    username: str,
    referer_id: int,
    user_first_name: str,
    referrals_total: int = None,
):
    """Adds a new user to the database, separating data into User and Referral tables.

    Args:
        session: A SQLAlchemy asynchronous session object.
        user_id: The unique identifier for the new user.
        referer_id: The ID of the user who referred this new user.
        user_first_name: The first name of the new user.
        referrals_total: The total number of referrals for this user.
    """

    new_user = User(
        user_id=user_id,
        user_first_name=user_first_name,
        username=username,
    )
    session.add(new_user)

    new_referral = Referral(
        user_id=user_id,
        referer_id=referer_id,
        is_verified=False,
    )
    session.add(new_referral)

    await session.commit()


async def orm_get_referer_referrals_total(session: AsyncSession, referer_id):
    query = (
        select(Referral.referrals_verified)
        .where(Referral.user_id == referer_id))
    result = await session.execute(query)
    return result.scalar()


async def orm_get_referer(session: AsyncSession, user_id):
    query = select(Referral).where(Referral.referer_id == user_id)
    result = await session.execute(query)
    return result.scalar_one_or_none()


async def orm_verify_referral(session: AsyncSession, user_id):
    """Подтверждает реферала"""
    query = update(Referral).where(Referral.user_id == user_id).values(is_verified=True)

    await session.execute(query)
    await session.commit()

async def count_verified_referrals(session: AsyncSession, referer_id: int) -> int:
    """Counts the number of verified referrals for a given referer_id (less efficient)."""
    try:
        referrals = await session.execute(
            select(Referral)
            .where(Referral.referer_id == referer_id, Referral.is_verified == True)
        )
        return len(referrals.scalars().all())  # Count in Python
    except SQLAlchemyError as e:
        print(f"Error counting verified referrals: {e}")
        return 0


async def orm_update_referer_amount(session: AsyncSession, referer_id: int, referrals_total: int):
    query = update(Referral).where(Referral.user_id == referer_id).values(
        referrals_total=referrals_total,
    )
    await session.execute(query)
    await session.commit()


async def add_referer_amount(referer_id: int, session: AsyncSession):
    referrals_total = await orm_get_referer_referrals_total(
        session=session,
        referer_id=referer_id
    )

    referrals_total = referrals_total + 1

    await orm_update_referer_amount(
        session=session,
        referer_id=referer_id,
        referrals_total=referrals_total
    )

async def add_money(session: AsyncSession, user_id: int):
    try:
        # Use update() to directly update the balance instead of fetching.
        await session.execute(
            update(User)
            .where(User.user_id == user_id)
            .values(balance=User.balance + MONEY_AMOUNT)
            .returning(User.balance)  # Return new balance for possible logging
        )
        await session.commit()

    except NoResultFound:
        print(f"User with ID {user_id} not found.")
    except Exception as e:
        print(f"Error adding money to user {user_id}: {e}")
        await session.rollback()

async def orm_get_channels():
    async with session_maker() as session:
        query = select(
            Channel.id,
            Channel.channel_id,
            Channel.channel_name,
            Channel.channel_address,
            Channel.channel_link
        )
        channels = await session.execute(query)
        return [dict(zip(('id', 'channel_id', 'channel_name', 'channel_address', 'channel_link'), row)) for row in channels]


async def orm_update_link_channel(session, channel_id, new_link):
    try:
        channel = await session.get(Channel, channel_id)
        if channel:
            channel.channel_link = new_link
            await session.commit() #Commit happens here, managed by the framework's session.
            return True
        else:
            return False
    except Exception as e:
        await session.rollback() #Rollback if something goes wrong.
        raise #Reraise for higher-level handling.   


async def orm_add_user_request(session: AsyncSession, user_id: int, channel_id: int):
    existing_request = await session.execute(
        select(ChannelRequests).where(
            ChannelRequests.channel_id == channel_id,
            ChannelRequests.user_id == user_id
        )
    )
    existing_request = existing_request.scalars().first()
    print(f"Exists or not - {existing_request}")

    if not existing_request:
        try:
            print(f"Try to add new req to join ORM query")
            new_request = ChannelRequests(
                channel_id=channel_id,
                user_id=user_id,
            )
            session.add(new_request)
            await session.commit()
        except Exception as e: 
            print(f"Error adding new req to join ORM query - {e}")
    else:
        # Handle the case where a request already exists.  You might log it,
        # return an error, or simply do nothing.  Choose based on your needs.
        print(f"Request already exists for user {user_id} and channel {channel_id}")

async def orm_check_user_request(session: AsyncSession, chat_id, user_id):
    query = select(ChannelRequests).where(ChannelRequests.user_id == user_id, ChannelRequests.channel_id == chat_id)
    res = await session.execute(query)

    res = res.scalars().first()

    return None if not res else True


async def orm_create_bid(session: AsyncSession, user_id: int, data):
    new_bid = UserHistory(
        user_id=user_id,
        amount=data["amount"],
        token=data["currency"],
        address=data["address"],
        status="🔄 В обработке"
    )

    session.add(new_bid)

    await session.commit()

    # обновляем баланс пользователя
    query = select(User).where(User.user_id == user_id)

    user = await session.execute(query)

    # Use fetchone() to get the first result
    user = user.scalar_one_or_none()

    user.balance -= float(data["amount"])

    await session.commit()


async def orm_get_history(session: AsyncSession, user_id: int):
    query = select(UserHistory).where(UserHistory.user_id == user_id, UserHistory.status == "🔄 В обработке")

    history = await session.execute(query)

    return history.scalars().all()


async def orm_get_all_bids(session: AsyncSession, user_id: int):
    query = select(UserHistory).where(UserHistory.user_id == user_id)

    history = await session.execute(query)

    return history.scalars().all()


async def orm_get_bid(session: AsyncSession, bid_id: int):
    query = select(UserHistory).where(UserHistory.id == bid_id)

    bid = await session.execute(query)

    return bid.scalar_one_or_none()


async def orm_get_bid_admin(session: AsyncSession, bid_id: int):
    query = (select(UserHistory)
             .where(UserHistory.id == bid_id)
             .join(User, UserHistory.user_id == User.user_id)
             .options(joinedload(UserHistory.user))
             )

    bid = await session.execute(query)

    return bid.scalar()


async def orm_withdraw_bid(session: AsyncSession, bid_id: int, answer: str):
    q = update(UserHistory).where(UserHistory.id == bid_id).values(
        answer=answer,
        status="✅ Успешно"
    )
    await session.execute(q)
    await session.commit()



async def orm_get_bids(session: AsyncSession):
    query = (select(UserHistory)
             .join(User, UserHistory.user_id == User.user_id)
             .options(joinedload(UserHistory.user))
             .where(UserHistory.status == "🔄 В обработке")
             )

    bids = await session.execute(query)
    all_bids = []

    for bid in bids.scalars().all():
        all_bids.append(bid.__dict__)

    return all_bids


async def orm_get_bids_all(session: AsyncSession):
    query = (select(UserHistory)
             .join(User, UserHistory.user_id == User.user_id)
             .options(joinedload(UserHistory.user))
             .where(UserHistory.status != "🔄 В обработке")
             )

    bids = await session.execute(query)
    all_bids = []

    for bid in bids.scalars().all():
        all_bids.append(bid.__dict__)

    return all_bids


async def orm_get_help_messages(session: AsyncSession, limit: int = 10, offset: int = 0):
    """Fetches help messages with pagination."""
    try:
        query = (select(HelpMessage, User)
                 .join(User, HelpMessage.user_id == User.user_id)
                 .limit(limit)
                 .offset(offset)
                 )
        query = query.where(HelpMessage.answer == "")

        result = await session.execute(query)

        help_messages = []
        for help_message, user in result.fetchall():  # Iterate and create tuples
            help_messages.append((help_message, user))
        return help_messages
    except SQLAlchemyError as e:
        print(f"Database error fetching help messages: {e}")
        return []  # Return an empty list on error


async def orm_get_help_mess(session, id):
    query = (select(HelpMessage, User)
             .join(User, HelpMessage.user_id == User.user_id)
             .where(HelpMessage.id == id, HelpMessage.answer == "")
             )

    try:
        result = await session.execute(query)
        help_mess = []
        for help_message, user in result.fetchall():  # Iterate and create tuples
            help_mess.append((help_message, user))
        return help_mess
    except MultipleResultsFound:
        print(f"Multiple help messages found for id {id}")
        return None  # Or raise a custom exception
    except SQLAlchemyError as e:
        print(f"Database error fetching help message for id {id}: {e}")
        return None  # Or raise a custom exception


async def orm_answer_help_msg(session: AsyncSession, id: int, text: str):
    query = (update(HelpMessage)
            .where(HelpMessage.id == id)
            .values(answer=text))

    await session.execute(query)
    await session.commit()


async def orm_get_help_messages_all(session: AsyncSession):
    query = (select(HelpMessage)
            .join(User, HelpMessage.user_id == User.user_id)
            )

    help_messages = await session.execute(query)

    return help_messages.scalars().all()


async def orm_get_last_help(session: AsyncSession, user_id: int):
    query = (select(HelpMessage)
             .where(HelpMessage.user_id == user_id)
             .order_by(desc(HelpMessage.created))  # Order by created timestamp descending
             .limit(1)
             )

    result = await session.execute(query)
    return result.scalar()




async def orm_close_bid(session: AsyncSession, bid_id: int, user_id) -> bool:
    query = select(UserHistory).where(UserHistory.id == bid_id)

    res = await session.execute(query)
    bid = res.scalar_one_or_none()

    if not bid:
        return False

    user = await orm_get_user(session, user_id)
    # возвращаем деньги на баланс
    user.balance += bid.amount

    await session.commit()
    try:
        await session.execute(delete(UserHistory).where(UserHistory.id == bid_id))
        await session.commit()
    except Exception as e:
        print(f"error: {e}")
        return False

    return True


async def orm_deny_bid(session: AsyncSession, bid_id: int):
    # Efficiently fetch the User object and UserHistory in a single query.
    try:
        query = select(UserHistory, User).join(User, UserHistory.user_id == User.user_id).where(
            UserHistory.id == bid_id).options(joinedload(UserHistory.user))
        res = await session.execute(query)
        bid_row, user_row = res.one_or_none()

        if not bid_row:
            return False

        if bid_row.status == "❌ Отклонена":
            return False  # Bid already rejected

        # update user balance
        user_row.balance += bid_row.amount

        # Update bid status
        query = update(UserHistory).where(UserHistory.id == bid_id).values(status="❌ Отклонена")
        await session.execute(query)

        await session.commit()
        return True
    except Exception as e:
        print(f"error: {e}")
        return False


async def orm_get_admins(session):
    query = select(User.user_id).where(User.is_admin == True)
    admins = await session.execute(query)

    return admins.scalars().all()


async def orm_add_channel(session: AsyncSession, chat_id, chat_title, chat_link, chat_username):
    # if not chat_username:
    #     chat_username = "None"

    channel = Channel(
        channel_id=chat_id,
        channel_name=chat_title,
        channel_address=chat_username,
        channel_link=chat_link,
    )

    session.add(channel)
    await session.commit()


async def orm_delete_channel(session: AsyncSession, channel_id):
    query = delete(Channel).where(Channel.channel_id == channel_id)

    await session.execute(query)
    await session.commit()


async def orm_get_users_id(session: AsyncSession):
    query = select(User.user_id)
    users = await session.execute(query)

    return users.scalars().all()


async def orm_get_users(session: AsyncSession):
    query = select(User)

    users = await session.execute(query)

    return users.scalars().all()


async def orm_change_user_balance(session: AsyncSession, user_id: int, new_balance: float):
    query = update(User).where(User.user_id == user_id).values(balance=new_balance)

    await session.execute(query)
    await session.commit()


async def orm_get_user_help_bid(session: AsyncSession, user_id: int):
    query = (select(HelpMessage).where(HelpMessage.user_id == user_id))
    user_help_message = await session.execute(query)

    return user_help_message.scalars().all()


async def orm_create_help_message(session: AsyncSession, user_id: int, text: str, message_id: int):
    new_help = HelpMessage(
        user_id=user_id,
        text=text,
        message_id=message_id
    )
    session.add(new_help)
    await session.commit()

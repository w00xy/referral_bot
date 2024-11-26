
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util import merge_lists_w_ordering

from database.orm_query import *
from filters.chat_types import IsSubscribedFilter, ChatTypeFilter
from handlers.start.new_user import handle_new_user
from kbds.kbs import *
from utils.texts import *

check_sub_router = Router()
check_sub_router.message.filter(ChatTypeFilter(["private"]))
check_sub_router.callback_query(ChatTypeFilter(["private"]))

@check_sub_router.message(CommandStart())
async def not_subscribed(message: types.Message, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username
    channels = await orm_get_channels()
    print(f"Пробуем добавить нового юзера - {user_id}")
    try:
        if message.text.__contains__("/start"):
            referer_id = None if message.text[7:] == '' else message.text[7:]

        try:
            user = await orm_get_user(session, user_id)
        except Exception as e:
            user = None
            print(f"Error not_subscribed orm_get_user  - {e}")

        if not user:
            print(f"Добавляем в бд нового юзера")
            try:
                await handle_new_user(message, session, state, user_id, first_name, referer_id)
            except Exception as e:
                print(f"Error not_subscribed handle_new_user - {e}")

            return

        # if user.username != username or user.user_first_name != first_name:
        #     user.first_name = first_name
        #     user.username = username
        #
        #     await session.commit()

        await message.answer(
            text=await get_subscribe_text(),
            reply_markup=await get_channels_btns(),
        )
    except Exception as e:
        print(f"Error not_subscribed - {e}")

@check_sub_router.callback_query(F.data == "check_subscribe")
async def check_sub_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()
    user_id = call.from_user.id
    first_name = call.from_user.first_name
    user = await orm_get_user(session, user_id)

    if not user:
        await handle_new_user(call.message, session, state, user_id, first_name, None)
        print(f"check_sub_router.callback_query error no user")
        return

    await call.message.answer(
        text=await get_subscribe_text(),
        reply_markup=await get_channels_btns(),
    )

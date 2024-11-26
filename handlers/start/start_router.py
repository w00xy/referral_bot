from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import *
from filters.chat_types import IsSubscribedFilter, ChatTypeFilter
from handlers.start.new_user import handle_new_user, verify_user
from kbds.kbs import *
from utils.texts import *

start_router = Router()
start_router.message.filter(ChatTypeFilter(["private"]), IsSubscribedFilter())
start_router.callback_query.filter(IsSubscribedFilter())

@start_router.message(CommandStart())
async def start_answer_bot(message: types.Message, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    referer_id = None if message.text[7:] == '' else message.text[7:]
    try:
        user = await orm_get_user(session, user_id)

    except Exception as e:
        user = None

    if not user:
        await handle_new_user(message, session, state, user_id, first_name, referer_id)
        return

    if user.username != username or user.user_first_name != first_name:
        user.first_name = first_name
        user.username = username

        await session.commit()

    try:
        print("Пробуем обновить подверидть реферала и обновить баланс")
        await verify_user(message, session, user)
    except Exception as e:
        print(f"Не смогли подвердить рефа ошибка - {e}")

    total_verified_refs = await count_verified_referrals(session, user_id)

    await message.answer(
        text=await get_start_text(user_id, total_verified_refs, user.balance),
        reply_markup=await get_start_buttons(user_id)
    )


@start_router.callback_query(F.data == "check_subscribe")
async def check_sub_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()

    user_id = call.from_user.id
    first_name = call.from_user.first_name

    try:
        user = await orm_get_user(session, user_id)

        print(f"GOT NEW USER ON REF - {user.user_id}")
    except Exception as e:
        user = None
        print(e)

    if not user:
        await handle_new_user(call.message, session, state, user_id, first_name)
        return

    if user.username != call.from_user.username or user.user_first_name != first_name:
        user.first_name = first_name
        user.username = call.from_user.username

        await session.commit()

    try:
        print("Пробуем обновить подверидть реферала и обновить баланс")
        await verify_user(call, session, user)
    except Exception as e:
        print(f"Не смогли подвердить рефа ошибка - {e}")

    total_verified_refs = await count_verified_referrals(session, user_id)

    await call.message.edit_text(
        text=await get_start_text(user_id, total_verified_refs, user.balance),
        reply_markup=await get_start_buttons(user_id)
    )


@start_router.callback_query(F.data == "refresh")
async def check_sub_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()
    await state.clear()

    user_id = call.from_user.id
    first_name = call.from_user.first_name

    try:
        user = await orm_get_user(session, user_id)

        if user.username != call.from_user.username or user.user_first_name != first_name:
            user.first_name = first_name
            user.username = call.from_user.username

            await session.commit()

    except Exception as e:
        user = None

    if not user:
        await handle_new_user(call, session, state, user_id, first_name)
        return

    try:
        total_verified_refs = await count_verified_referrals(session, user_id)

        await call.message.edit_text(
            text=await get_start_text(user_id, total_verified_refs, user.balance),
            reply_markup=await get_start_buttons(user_id)
        )
    except Exception:
        pass
import asyncio

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config import MIN_BALANCE_CRYPTO, MAX_BIDS
from database.orm_query import orm_create_help_message, orm_get_user_help_bid, orm_get_help_mess, orm_get_last_help
from filters.chat_types import IsSubscribedFilter, ChatTypeFilter, IsAdmin
from handlers.user_logic.admin_notify import admin_notify_help
from kbds.kbs import *
from states.user_states import UserStates
from utils.texts import *

user_help_router = Router()


@user_help_router.callback_query(F.data.startswith("user_help_bid_"))
async def user_help_bid_start(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    user_id = call.from_user.id
    await call.answer()
    # Проверяем что у пользователя еще нет открытой заявки в поддержку
    user_help_bids = await orm_get_user_help_bid(session, user_id)
    for user_help in user_help_bids:
        if user_help.answer != "":
            await call.message.answer(
                text=await admin_answer_help_text(user_help)
            )
        else:
            await call.message.answer(
                text=await already_has_help_message_text(user_help),
                reply_markup=home_button
            )
            return


    await call.message.answer(
        text=user_help_start_mess,
        reply_markup=home_button
    )

    await state.set_state(UserStates.help)


@user_help_router.message(UserStates.help, F.text)
async def user_help_bid_message(message: types.Message, session: AsyncSession, state: FSMContext):
    text = message.text
    user_id = message.from_user.id
    message_id = message.message_id

    # Проверяем что у пользователя еще нет открытой заявки в поддержку
    user_help_bids = await orm_get_user_help_bid(session, user_id)

    try:
        await orm_create_help_message(session, user_id, text, message_id)

        last_help_msg = await orm_get_last_help(session, user_id)

        await admin_notify_help(message, session, last_help_msg)

        await message.answer(
            text=await user_help_added_text(text, user_id),
            reply_markup=home_button
        )
    except Exception as e:
        await message.answer(
            f"Произошла непредвиденная ошибка.\nПопробуйте снова позже!"
        )
        print(f"Exception during help message creation: {e}")

    await state.clear()

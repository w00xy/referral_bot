import asyncio
import datetime
from datetime import time
from typing import Union

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.loggers import event
from pyexpat.errors import messages
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util import await_only

from database.orm_query import orm_get_user, orm_add_user, orm_get_users_id
from filters.chat_types import IsAdmin, ChatTypeFilter
from handlers.admin.channels_router import channel_router
from kbds.kbs import *
from states.admin_states import Admin
from states.user_states import *
from utils.texts import *


spam_router = Router()


@spam_router.callback_query(F.data == "spam")
async def spam_handler(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()

    await call.message.edit_text(
        f"Отправьте сообщение которое будет рассылаться(Можно отправить фото с текстом)",
        reply_markup=await get_back_to_admin()
    )
    await state.set_state(Admin.edit_spam)


@spam_router.message(Admin.edit_spam)
async def check_spam_post(mess: types.Message, session: AsyncSession, state: FSMContext):

    mess_spam_id = mess.message_id

    try:
        await mess.bot.copy_message(chat_id=mess.chat.id, from_chat_id=mess.chat.id, message_id=mess_spam_id, reply_markup=await get_start_spam_btns())

    except Exception as e:
        print(e)

    await state.set_data({
        "mess_spam_id": mess_spam_id
    })
    await state.set_state(Admin.start_spam)


@spam_router.message(Admin.start_spam)
@spam_router.callback_query(Admin.start_spam, F.data == "confirm_spam")
async def edit_spam(event: Union[types.CallbackQuery, types.Message], session: AsyncSession, state: FSMContext):
    users_id = await orm_get_users_id(session)
    print(users_id)
    total_users = len(users_id)
    success = 0
    sleep_time = 0.15
    start_time = datetime.datetime.now()
    estimated_end_time = start_time + datetime.timedelta(seconds=total_users * sleep_time)
    mess_spam_id = await state.get_value("mess_spam_id")

    if isinstance(event, types.CallbackQuery):
        await event.answer()
        mess = event.message
    else:
        mess = event

    await mess.answer(
        text=f"📬 Информация о рассылке:\n"
             f"👥 Всего пользоваталей: {total_users}\n"
             f"⏳ Время начала: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
             f"🕒 Примерное время окончания: {estimated_end_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

    for user_id in users_id:
        try:
            await mess.bot.copy_message(chat_id=user_id, from_chat_id=mess.chat.id, message_id=mess_spam_id)
            success += 1
        except Exception as e:
            print(e)
        finally:
            await asyncio.sleep(sleep_time)

    await state.clear()

    fact_end_time = datetime.datetime.now()

    await mess.answer(
        text=f"📬 Информация о рассылке:\n"
             f"👥 Всего пользоваталей: {total_users}\n"
             f"✅ Успешно доставлено до: {success}\n"
             f"❌ Не доставлено до: {total_users - success}\n"
             f"⏳ Время начала: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
             f"🕒 Фактическое время окончания: {fact_end_time.strftime('%Y-%m-%d %H:%M:%S')}"
    )

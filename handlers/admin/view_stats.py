from typing import Union

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util.langhelpers import repr_tuple_names

from database.orm_query import orm_get_bids, orm_close_bid, orm_deny_bid, orm_get_user, orm_get_users, orm_get_history, \
    orm_get_all_bids, orm_change_user_balance
from filters.chat_types import IsAdmin, ChatTypeFilter
from kbds.kbs import *
from states.admin_states import Admin
from states.user_states import *
from utils.texts import *


view_stats_router = Router()



@view_stats_router.callback_query(F.data.startswith("view_stats"))
async def view_stats_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    try:
        users = await orm_get_users(session)
        for user in users:
            print(user.user_id)
    except Exception as e:
        print(e)
        await call.message.answer(f"Ошибка при получении пользоваталей: {e}")
        return

    await call.answer()
    try:
        slide = int(call.data.split("_")[-1])
    except ValueError:
        slide = 0

    await call.message.edit_text(
        text=await users_text(users, slide),
        reply_markup=await users_buttons(slide, total_users=len(users)),
    )

    await state.set_state(Admin.search_stats)

@view_stats_router.callback_query(F.data.startswith("user_detailed_stats_"))
@view_stats_router.message(Admin.search_stats, F.text)
async def user_stats_bot(event: Union[types.Message, types.CallbackQuery], session: AsyncSession, state: FSMContext):
    mess = event
    if isinstance(event, types.CallbackQuery):
        await event.answer()
        await state.clear()
        mess = event.message
        search_id = event.data.split("_")[-1]

    if isinstance(event, types.Message):
        try:
            search_id = int(mess.text)
        except ValueError:
            await mess.answer(f"Что бы найти информацию о юзере отправьте его id (Пример: 1072341012)")
            return

    user = await orm_get_user(session, search_id)

    await mess.answer(
        text=await detailed_info_user_text(user),
        reply_markup=await detailed_info_user_buttons(user)
    )

@view_stats_router.callback_query(F.data.startswith("get_user_bids"))
async def get_user_bids_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    search_id = int(call.data.split("_")[-1])
    await call.answer()
    bids = await orm_get_history(session, search_id)

    last_bid = len(bids)

    if not bids:
        await call.message.answer(
            text=no_bids_text,
        )

    for i, bid in enumerate(bids):
        await call.message.answer(
            text=await get_bid_text(bid),
            reply_markup=await user_bid_admin_buttons(search_id, bid, last_bid, i)
        )


@view_stats_router.callback_query(F.data.startswith("get_user_all_bids_"))
async def get_user_all_bids(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    search_id = int(call.data.split("_")[-1])
    await call.answer()

    all_bids = await orm_get_all_bids(session, search_id)
    last_bid = len(all_bids)

    if not all_bids:
        await call.message.answer(
            text=no_bids_text,
        )

    for i, bid in enumerate(all_bids):
        await call.message.answer(
            text=await get_bid_text(bid),
            reply_markup=await user_bid_admin_buttons(search_id, bid, last_bid, i)
        )

@view_stats_router.callback_query(F.data.startswith("change_balance_"))
async def change_balance_user_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()
    await state.set_state(Admin.give_balance)
    user_id = call.data.split("_")[-1]

    await state.set_data({
        "user_id": user_id,
    })

    await call.message.answer("Введите какой будет баланс у пользователя: ", reply_markup=await deny_balance(user_id))


@view_stats_router.message(Admin.give_balance)
async def confirm_change_balance(mess: types.Message, session: AsyncSession, state: FSMContext):
    user_id = await state.get_value("user_id")

    try:
        new_balance = float(mess.text)
    except ValueError:
        await mess.answer(f"Можно ввести только цифры с плавающей точкой. Примеры (12 | 3.5 | 40)")
        return

    try:
        await orm_change_user_balance(session, user_id, new_balance)

        await mess.answer(f"✅ Баланс успешно изменен", reply_markup=await deny_balance(user_id))

    except Exception as e:
        await mess.answer(f"Произошла ошибка при смене баланса: {e}")
        return

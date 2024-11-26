import asyncio

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config import MIN_BALANCE_CRYPTO, MAX_BIDS
from database.orm_query import *
from filters.chat_types import IsSubscribedFilter, ChatTypeFilter, IsAdmin
from handlers.user_logic.fake_traffic import fake_traffic_router
from handlers.user_logic.user_help import user_help_router
from kbds.kbs import *
from states.user_states import Withdraw
from utils.texts import *

user_router = Router()
user_router.message.filter(ChatTypeFilter(["private"]), IsSubscribedFilter())
user_router.callback_query.filter(IsSubscribedFilter())

user_router.include_router(user_help_router)
user_router.include_router(fake_traffic_router)

@user_router.callback_query(F.data == "want_withdraw")
async def handle_user_query_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):

    user_id = call.from_user.id
    user = await orm_get_user(session, user_id)

    # Проверка на количество открытых заявок. Максимум 3
    try:
        user_history = await orm_get_history(session, user_id)
        total_bids = len(user_history)

        if total_bids >= MAX_BIDS:
            await call.answer(
                text=max_limit_bids_text,
                show_alert=True,
            )
            return
    except Exception as e:
        pass

    # Баланс больше минимальной суммы вывода
    if user.balance >= MIN_BALANCE_CRYPTO:
        await call.answer()
        await state.set_state(Withdraw.select_currency)

        await call.message.edit_text(
            text=choose_method_text,
            reply_markup=choose_method_btns,
        )
        return

    await call.answer(f"Вывод доступен при балансе от {MIN_BALANCE_CRYPTO} USDT",
                      show_alert=True)



@user_router.callback_query(F.data.startswith("currency_"), Withdraw.select_currency)
async def selected_currency_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    user_id = call.from_user.id
    user = await orm_get_user(session, user_id)
    cur = " ".join(call.data.split("_")[1:]).upper()
    # добавляем валюту в стейт
    await state.set_data({"currency": cur})
    print(f"USER: {user_id}, CUR: {cur}")
    await call.answer()
    await call.message.edit_text(
        text=await selected_currency_text(cur, user),
        reply_markup=back_to_choose_currency,
    )

    await state.set_state(Withdraw.enter_amount)


@user_router.message(Withdraw.enter_amount)
async def handle_amount(message: types.Message, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    user = await orm_get_user(session, user_id)

    amount = message.text

    try:
        amount = float(amount)
    except ValueError:
        await message.answer(f"<b>Введенная сумма не является числом!</b>")
        return

    if amount > user.balance:
        await message.answer(f"<b>Недостаточный баланс!</b>")
        return

    if amount < MIN_BALANCE_CRYPTO:
        await message.answer(f"<b>Минимальная сумма вывода: <i>{MIN_BALANCE_CRYPTO} USDT</i></b>")
        return

    await state.update_data({"amount": amount})

    data = await state.get_data()

    await message.answer(
        text=await get_address_text(cur=data["currency"], amount=amount),
        reply_markup=back_to_choose_currency
    )
    await state.set_state(Withdraw.enter_address)


@user_router.message(Withdraw.enter_address)
async def handle_address(message: types.Message, session: AsyncSession, state: FSMContext):
    user_id = message.from_user.id
    user = await orm_get_user(session, user_id)

    address = message.text

    if len(address) < 6 or len(address) > 70:
        await message.answer(f"<b>Неверный адрес</b>")
        return

    await state.update_data({"address": address})

    data = await state.get_data()

    await message.answer(
        text=await get_confirm_text(user, amount=data["amount"], cur=data["currency"], address=address),
        reply_markup=decline_bid
    )

    await state.set_state(Withdraw.confirm)

@user_router.callback_query(F.data == "send_bid", Withdraw.confirm)
async def withdraw_confirm_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    user_id = call.from_user.id
    user = await orm_get_user(session, user_id)

    data = await state.get_data()

    await orm_create_bid(session, user_id, data)

    await call.answer()
    await call.message.answer(
        text=sent_bid_text,
    )

    await asyncio.sleep(2)
    total_verified_refs = await count_verified_referrals(session, user_id)

    await call.message.answer(
        text=await get_start_text(user_id, total_verified_refs, user.balance),
        reply_markup=await get_start_buttons(user_id)
    )


@user_router.callback_query(F.data == "get_history")
async def get_history_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await state.clear()
    await call.answer()
    user_id = call.from_user.id
    user_history = await orm_get_history(session, user_id)
    last_bid = len(user_history)

    if not user_history:
        await call.message.answer(
            text=no_bids_text,
        )
        return

    await call.message.delete()

    for i, bid in enumerate(user_history):
        await call.message.answer(
            text=await get_bid_text(bid),
            reply_markup=await get_bid_btns(call, bid, last_bid, i)
        )

@user_router.callback_query(F.data.startswith("close_bid_"))
async def cancel_bid(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id
    bid_id = int(call.data.split("_")[-1])

    try:
        bid = await orm_get_bid(session, bid_id)
    except ValueError:
        await call.answer("Произошла ошибка обратитесь в поддержку!")
        print(f"Ошибка получения заявки: {e}")
        return
    await call.answer()

    if not bid:
        await call.message.answer(
            text=await no_bid_text(bid_id),
        )
        return

    try:
        await orm_close_bid(session, bid_id, user_id)
    except Exception as e:
        await call.answer("Произошла ошибка при отмене заявки. Пожалуйста, попробуйте снова позже.")
        print(f"Ошибка при отмене заявки: {e}")
        return

    await call.message.answer(
        text=await bid_text(bid_id),
    )

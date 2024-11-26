from typing import Union

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_bids, orm_close_bid, orm_deny_bid, orm_get_bid, orm_get_bid_admin, \
    orm_withdraw_bid, orm_get_bids_all
from filters.chat_types import IsAdmin, ChatTypeFilter
from kbds.kbs import *
from states.admin_states import Admin
from states.user_states import *
from utils.extra import send_check_user
from utils.texts import *


view_bids_router = Router()


@view_bids_router.callback_query(F.data.startswith("view_bids"))
async def view_bids_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    bids = await orm_get_bids(session)
    await call.answer()

    try:
        slide = int(call.data.split("_")[-1])
    except ValueError:
        slide = 0
    try:
        await call.message.edit_text(
            text=await bids_text(bids, slide),
            reply_markup=await bids_buttons(slide, total_bids=len(bids)),
        )

        await state.set_state(Admin.search_bids)
    except:
        await call.answer("Заявок не обнаружено")


@view_bids_router.callback_query(F.data.startswith("closed_bids"))
async def view_bids_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    bids = await orm_get_bids_all(session)
    await call.answer()

    try:
        slide = int(call.data.split("_")[-1])
    except ValueError:
        slide = 0
    try:
        await call.message.edit_text(
            text=await bids_text(bids, slide),
            reply_markup=await closed_bids_btns(slide, total_bids=len(bids)),
        )

        await state.set_state(Admin.search_bids)
    except:
        await call.answer("Заявок не обнаружено")


@view_bids_router.callback_query(F.data.startswith("deny_bid_"))
@view_bids_router.message(F.text.startswith("/deny_bid_"), Admin.search_bids)
async def handle_deny_bid_admin(event: Union[types.Message, types.CallbackQuery], session: AsyncSession, state: FSMContext):
    mess = event
    if isinstance(event, types.CallbackQuery):
        await event.answer()
        bid_id = int(event.data.split("_")[-1])
        mess = event.message
    if isinstance(event, types.Message):
        bid_id = int(mess.text.split("_")[-1])

    try:
        was_denied = await orm_deny_bid(session, bid_id)
        if was_denied:
            await mess.answer(
                f"📝<b> Заявка {bid_id} (Для юзера {bid_id + FAKE_BIDS})</b>\n"
                f"<b>Новый статус: <i>❌ Отклонена</i></b>"
            )
            return
        await mess.answer(
            f"Не смогли отменить заявку.\nЗаявки с id {bid_id} (Для юзера {bid_id + FAKE_BIDS}) не найдено ЛИБО уже Отменена"
        )
    except Exception as e:
        await mess.answer(
            f"Не смогли отменить заявку. Ошибка: {e}"
        )


@view_bids_router.message(F.text.startswith("/open_bid"), Admin.search_bids)
@view_bids_router.callback_query(F.data.startswith("open_bid"))
async def open_detailed_bid_info(event: Union[types.CallbackQuery, types.Message], session: AsyncSession, state: FSMContext):
    if isinstance(event, types.Message):
        bid_id = int(event.text.split("_")[-1])

        mess = event
    elif isinstance(event, types.CallbackQuery):
        bid_id = int(event.data.split("_")[-1])

        await event.answer()
        mess = event.message
    else:
        return

    try:
        bid_info = await orm_get_bid_admin(session, bid_id)

        await mess.answer(
            text=await get_detailed_bid_text(bid_info),
            reply_markup=await get_detailed_bid_btns(bid_info)
        )
    except Exception as e:
        print(f"Error orm_get_bid - {e}")


@view_bids_router.callback_query(F.data.startswith("confirm_withdraw_"))
async def confirm_withdraw_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    bid_id = int(call.data.split("_")[-1])

    await call.answer()

    await call.message.answer(
        text=f"Отправьте сообщение которое будет доставлено пользователю (Чек @CryptoBot):"
    )

    await state.set_state(Admin.wait_check)
    await state.set_data({
        "bid_id": bid_id,
    })


@view_bids_router.message(Admin.wait_check)
async def handle_check_bot(mess: types.Message, session: AsyncSession, state: FSMContext):
    check = mess.text
    bid_id = await state.get_value("bid_id")

    await state.update_data({
        "check": check,
    })

    try:
        bid_info = await orm_get_bid_admin(session, bid_id)
    except Exception as e:
        print(f"Error orm_get_bid - {e}")
        await mess.answer(f"Error orm_get_bid - {e}")
        return

    await mess.answer(
        text=await get_check_text(check, bid_info),
        reply_markup=await get_check_btns(bid_info)
    )

@view_bids_router.callback_query(F.data.startswith("send_check_"))
async def send_check_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    check = await state.get_value("check")
    bid_id = await state.get_value("bid_id")
    await call.answer()
    try:
        bid_info = await orm_get_bid_admin(session, bid_id)
    except Exception as e:
        print(f"Error orm_get_bid - {e}")
        await call.message.answer(f"Error orm_get_bid - {e}")
        return

    try:
        await orm_withdraw_bid(session, bid_id, check)
    except Exception as e:
        print(f"Error orm_withdraw_bid - {e}")
        await call.message.answer(f"Error orm_withdraw_bid - {e}")
        return

    try:
        await send_check_user(event=call, bid=bid_info, check=check)
    except Exception as e:
        print(f"Error send_check_user - {e}")
        await call.message.answer(f"Error send_check_user - {e}")
        return

    try:
        await call.message.answer(
            text="✅ Вывод осуществлен\n\n"
                 "Ответ отправлен пользователю, статус заявки изменен!",
            reply_markup=await get_back_to_bids()
        )
    except Exception as e:
        print(f"Error call.message.answer - {e}")
        await call.message.answer(f"Error call.message.answer - {e}")
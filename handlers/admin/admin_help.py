from multiprocessing.connection import Connection

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from config import BOT_ID
from database.orm_query import orm_get_help_mess, orm_get_help_messages, orm_answer_help_msg
from kbds.kbs import *
from states.admin_states import Admin
from states.user_states import *
from utils.texts import *


admin_help = Router()

# Обработка новых сообщений в поддержку
@admin_help.callback_query(F.data.startswith("help_menu"))
async def admin_help_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    try:
        slide = int(call.data.split("_")[-1])
        if slide < 0:
            slide = 0  # Clamp slide value to 0
    except (ValueError, IndexError):
        slide = 0

    try:
        help_messages = await orm_get_help_messages(session, limit=5, offset=slide * 5)

        for help_mes in help_messages:
            h, u = help_mes

            print(h, u)

        if not help_messages:
            await call.answer("No help messages found.")
            return

        print(f"Fetched {len(help_messages)} help messages.")

        await call.answer()
        await call.message.answer(
            text=await help_messages_text(help_messages, slide),
            reply_markup=await help_messages_btns(help_messages, slide),
        )

        await state.set_state(Admin.help_answer)

    except Exception as e:
        print(f"Error processing help messages: {e}")
        await call.answer("An error occurred. Please try again later.")


@admin_help.message(F.text.startswith("/help"), Admin.help_answer)
async def help_answer_user(mess: types.Message, session: AsyncSession, state: FSMContext):

    help_id = mess.text.split("_")[-1]

    try:
        help_mess = await orm_get_help_mess(session, help_id)
        print(f"Fetched help message for {help_mess}")
        await mess.answer(
            text=await help_text(help_mess),
            reply_markup=await help_user_btns(help_mess),
        )

    except Exception as e:

        print(f"Error processing help messages: {e}")
        await mess.answer(
            text=f"Error processing help messages: {e}",
        )

@admin_help.callback_query(F.data.startswith("answer_help_"))
async def answer_help_mess(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    help_id = call.data.split("_")[-1]
    await call.answer()

    await state.set_data({
        "help_id": help_id,
    })

    await call.message.answer(
        text=admin_wait_help_text
    )

    await state.set_state(Admin.wait_answer_help_text)


@admin_help.message(Admin.wait_answer_help_text)
async def handle_help_text(mess: types.Message, session: AsyncSession, state: FSMContext):
    admin_text = mess.text

    await state.update_data({
        "admin_text": admin_text,
    })
    help_id = await state.get_value("help_id")

    try:
        help_mess = await orm_get_help_mess(session, help_id)
        print(f"Fetched help message for {help_mess}")
    except Exception as e:

        print(f"Error processing help messages: {e}")
        await mess.answer(
            text=f"Error processing help messages: {e}",
        )
        return

    await mess.answer(
        text=await help_text_confirm(help_mess, admin_text),
        reply_markup=await confirm_answer_help_btns(help_mess),
    )

    await state.set_state(Admin.wait_answer_help_text)


@admin_help.callback_query(F.data.startswith("confirm_help_answer"))
async def handle_help_text(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    help_id = await state.get_value("help_id")
    admin_text = await state.get_value("admin_text")

    await call.answer()

    text = f"📨 Ответ от администратора\n\n"
    text += admin_text

    try:

        help_mess = await orm_get_help_mess(session, help_id)

        mess, user = help_mess[0]

        await call.bot.send_message(
            chat_id=mess.user_id,
            text=text
        )

        await orm_answer_help_msg(session, help_id, admin_text)

        await call.message.answer(
            text=help_answered_text,
            reply_markup=await only_admin_panel()
        )

    except Exception as e:
        await call.message.answer(f"Произошла ошибка при отправлении ответа: {e}")



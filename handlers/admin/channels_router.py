from typing import Union

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util import methods_equivalent, await_only

from config import BOT_ID
from database.orm_query import orm_add_channel, orm_delete_channel, orm_update_link_channel
from kbds.kbs import *
from states.admin_states import Admin
from states.user_states import *
from utils.texts import *


channel_router = Router()


@channel_router.callback_query(F.data == "handle_channels")
async def handle_channels(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    user_id = call.from_user.id
    await call.answer()
    await call.message.answer(
        text=f"<b>Что бы добавить новый канал:</b>\n\n"
             f"<b><i>1. Добавьте бота в канал в качестве Администратора</i></b>\n"
             f"<b><i>2. Нажмите на кнопку добавить канал ниже и выберите нужный канал</i></b>\n"
             f"<b><i>3. Измените ссылку для вступления в канал если требуется(Для закрытых это обязательно)</i></b>\n"
             f"<b><i>4. В конце нажмите кнопку *Добавить канал*</i></b>\n",
        reply_markup=await create_del_channel()
    )


@channel_router.message(F.chat_shared)
async def handle_chat_shared(message: types.Message, session: AsyncSession, state: FSMContext):

    chat_id = message.chat_shared.chat_id
    chat_username = message.chat_shared.username
    chat_title = message.chat_shared.title

    if chat_username:
        chat_link = f"https://t.me/{chat_username}"
    else:
        chat_link = f"ЗАКРЫТЫЙ КАНАЛ"

    bot_status = False
    try:
        bot_in_channel = await message.bot.get_chat_member(chat_id=chat_id, user_id=BOT_ID)
        print(bot_in_channel)
        if bot_in_channel.status == "administrator":
            bot_status = True
    except:
        pass

    if bot_status:
        await state.set_state(Admin.add_channel)
        await state.set_data({
            "chat_id": chat_id,
            "chat_username": chat_username,
            "chat_title": chat_title,
            "chat_link": chat_link,
            "bot_status": bot_status,
        })

        await message.answer(
            f"<b>{'✅ Бот является администратором' if bot_status else '❌ Бот не является администратором'}\n</b>"
            f"<b>Название канала: <i>{chat_title}</i></b>\n"
            f"<b>ID: <i>{chat_id}</i></b>\n"
            f"<b>Имя канала: <i>{'@' + chat_username if chat_username else chat_username}</i></b>\n"
            f"<b>Ссылка для вступления: <i>{chat_link}</i></b>",
            reply_markup=await handle_channel_btns(chat_link)
        )
        return

    await message.answer(
        f"<b>{'✅ Бот является администратором' if bot_status else '❌ Бот не является администратором'}\n</b>"
        f"<b>Название канала: <i>{chat_title}</i></b>\n"
        f"<b>ID: <i>{chat_id}</i></b>\n"
        f"<b>Имя канала: <i>{'@' + chat_username if chat_username else chat_username}</i></b>\n"
        f"<b>Ссылка для вступления: <i>{chat_link}</i></b>\n\n"
        f"<b>Бот должен быть администратором в канале что бы добавить его в список каналов с проверкой подписки!</b>",
    )

@channel_router.callback_query(F.data == "channel_change_link")
async def change_link_channel_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()
    await call.message.answer(
        f"Введите ссылку: "
    )

    await state.set_state(Admin.change_link)


@channel_router.message(Admin.change_link)
async def get_link_to_change_bot(message: types.Message, session: AsyncSession, state: FSMContext):
    new_link = message.text

    await state.update_data({
        "chat_link": new_link
    })

    chat_data = await state.get_data()

    bot_status = chat_data["bot_status"]
    chat_title = chat_data["chat_title"]
    chat_link = chat_data["chat_link"]
    chat_username = chat_data["chat_username"]
    chat_id = chat_data["chat_id"]

    await message.answer(
        f"<b>{'✅ Бот является администратором' if bot_status else '❌ Бот не является администратором'}\n</b>"
        f"<b>Название канала: <i>{chat_title}</i></b>\n"
        f"<b>ID: <i>{chat_id}</i></b>\n"
        f"<b>Имя канала: <i>{'@' + chat_username if chat_username else chat_username}</i></b>\n"
        f"<b>Ссылка для вступления: <i>{chat_link}</i></b>",
        reply_markup=await handle_channel_btns(chat_link)
    )
    await state.set_state(Admin.confirm_channel)


@channel_router.callback_query(F.data == "add_channel")
async def add_channel(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()
    chat_data = await state.get_data()

    bot_status = chat_data["bot_status"]
    chat_title = chat_data["chat_title"]
    chat_link = chat_data["chat_link"]
    chat_username = chat_data["chat_username"]
    chat_id = chat_data["chat_id"]
    try:
        await orm_add_channel(session, chat_id, chat_title, chat_link, chat_username)

        await call.message.answer(
            f"Канал успешно добавлен!\n\n"
            f"Можно проверить написав команду /start"
        )
    except Exception as e:
        await call.message.answer(
            f"Ошибка при добавлении канала: {e}"
        )
    await state.clear()

@channel_router.message(F.text == "Просмотреть каналы")
async def choose_delete_channel_bot(message: types.Message, session: AsyncSession, state: FSMContext):

    channels = await orm_get_channels()

    if not channels:
        await message.answer(f"Каналов не найдено")

    for channel in channels:
        chat_id = channel['channel_id']
        chat_username = channel["channel_address"]
        await message.answer(
            f"Название канала: {channel['channel_name']}\n"
            f"ID Канала: {chat_id}\n"
            f"Имя канала: <i>{'@' + chat_username if chat_username else chat_username}</i>\n"
            f"Ссылка на канал: {channel['channel_link']}",
            reply_markup=await delete_channel_button(chat_id)
        )


@channel_router.callback_query(F.data.startswith("delete_channel"))
async def delete_channel_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()

    channel_id = call.data.split("_")[-1]

    print("Удаляем канал Channel ID -", channel_id)

    try:
        await orm_delete_channel(session, channel_id)

        await call.message.answer(
            f"Канал успешно удален!",
        )
    except Exception as e:

        await call.message.answer(
            f"Ошибка при удалении канала: {e}"
        )
        
@channel_router.callback_query(F.data.startswith("update_channel_link_"))
async def update_link_channel_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()
    channel_id = call.data.split("_")[-1]
    
    await call.message.answer(f"Введите новую ссылку: ")
    
    await state.set_state(Admin.update_link)
    await state.set_data({
        "channel_id": channel_id
    })
        
        
@channel_router.message(Admin.update_link)
async def update_link_channel_bot(mess: types.Message, session: AsyncSession, state: FSMContext):
    channel_id = await state.get_value("channel_id")
    new_link = mess.text
    print(f"ОБНОВЛЕНИЕ ССЫЛКИ - {channel_id} | {new_link}")
    try:
        is_updated = await orm_update_link_channel(session, channel_id, new_link) # orm_update_link_channel should NOT start a new transaction

        if is_updated:
            await mess.answer(f"Ссылка успешно обновлена")
        else:
            await mess.answer(f"Не смогли обновить ссылку. Канал не найден в бд")
    except Exception as e:
        await mess.answer(f"Не смогли обновить ссылку: {e}")
from typing import Union

from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.loggers import event
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_user, orm_add_user
from filters.chat_types import IsAdmin, ChatTypeFilter
from handlers.admin.admin_help import admin_help
from handlers.admin.channels_router import channel_router
from handlers.admin.spam_router import spam_router
from handlers.admin.view_bids import view_bids_router
from handlers.admin.view_stats import view_stats_router
from kbds.kbs import *
from states.admin_states import Admin
from states.user_states import *
from utils.texts import *


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())
admin_router.callback_query.filter(IsAdmin())

admin_router.include_router(channel_router)
admin_router.include_router(spam_router)
admin_router.include_router(view_bids_router)
admin_router.include_router(view_stats_router)
admin_router.include_router(admin_help)


@admin_router.message(Command("admin"))
@admin_router.callback_query(F.data == "admin_panel")
async def handle_admin(event: Union[types.CallbackQuery, types.Message], session: AsyncSession, state: FSMContext):
    # await state.clear()

    first_name = event.from_user.first_name
    last_name = event.from_user.last_name

    if isinstance(event, types.CallbackQuery):
        await event.answer()
        event = event.message

    await event.answer(
        text=f"<b>Добро пожаловать, {first_name} {last_name if last_name else ''}</b>",
        reply_markup=await get_admin_panel()
    )

@admin_router.callback_query(F.data == "add_admin")
async def add_admin_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()

    await call.message.answer(
        f"Введите ID пользователя: "
    )

    await state.set_state(Admin.add_admin)


@admin_router.message(Admin.add_admin)
async def handle_add_admin(mess: types.Message, session: AsyncSession, state: FSMContext):
    new_admin_id = mess.text

    try:
        new_admin_id = int(new_admin_id)
    except ValueError:
        await mess.answer(f"❌ ID должен состоять только из цифр")
        return

    try:
        user = await orm_get_user(session, new_admin_id)
    except ValueError:
        await mess.answer(f"❌ Пользователя с таким id не найдено в БД")
        return

    await state.set_state(Admin.grant_admin)
    if user.is_admin:
        await mess.answer(f"Имя: {user.user_first_name}\n"
                          f"Юзер: {'@' + user.username if user.username else 'Нет юзернейма'}\n"
                          f"ID: {user.user_id}\n"
                          f"Баланс: {user.balance}\n"
                          f"Статус: {'Admin' if user.is_admin else 'User'}",
                          )
        return
    await mess.answer(f"Имя: {user.user_first_name}\n"
                      f"Юзер: {'@' + user.username if user.username else 'Нет юзернейма'}\n"
                      f"ID: {user.user_id}\n"
                      f"Баланс: {user.balance}\n"
                      f"Статус: {'Admin' if user.is_admin else 'User'}",
                      reply_markup=await get_grant_admin(user.user_id)
                      )



@admin_router.callback_query(F.data.startswith("grant_admin"))
async def grant_admin(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()
    try:
        new_admin_id = int(call.data.split("_")[-1])
    except ValueError as e:
        print(e)
        return

    try:
        user = await orm_get_user(session, new_admin_id)
    except ValueError:
        await call.message.answer(f"❌ Пользователя с таким id не найдено в БД")
        return

    if user.is_admin:
        await call.message.answer(f"❌ Пользователя уже является администратором")
        return

    try:
        user.is_admin = True
        await session.commit()

        await call.message.answer(f"✅ Пользователь {'@' + user.username if user.username else 'Нет юзернейма'} теперь администратор")
    except ValueError as e:
        await call.message.answer(f"❌ Ошибка при присваивании прав админа: {e}")


@admin_router.callback_query(F.data.startswith("remove_admin_"))
async def remove_admin(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()

    try:
        user_id = int(call.data.split("_")[-1])
    except ValueError as e:
        print(e)
        return

    try:
        user = await orm_get_user(session, user_id)
    except ValueError:
        await call.message.answer(f"❌ Пользователя с таким id не найдено в БД")
        return

    if user.is_admin:
        try:
            user.is_admin = False
            await session.commit()

            await call.message.answer(f"✅ Пользователь {'@' + user.username if user.username else 'Нет юзернейма'} теперь не является Админом!")
            return
        except ValueError as e:
            await call.message.answer(f"❌ Ошибка при присваивании прав админа: {e}")

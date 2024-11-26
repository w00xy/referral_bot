from abc import ABC
from typing import Union

from aiogram.filters import Filter
from aiogram import Bot, types
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import orm_get_channels, orm_check_user_request, orm_get_admins


class ChatTypeFilter(Filter):
    def __init__(self, chat_types: list[str]) -> None:
        self.chat_types = chat_types

    async def __call__(self, message: types.Message) -> bool:
        return message.chat.type in self.chat_types


class IsAdmin(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, event: Union[types.Message, types.CallbackQuery], bot: Bot, session: AsyncSession) -> bool:
        admins_list = []
        try:
            admins_list = await orm_get_admins(session)
            print(f"ID админов: {admins_list}")
        except Exception as e:
            print(f"Ошибка при получении админов: {e}")

        return event.from_user.id in admins_list


# Фильтр проверки подписки
class IsSubscribedFilter(Filter):
    def __init__(self) -> None:
        pass

    async def __call__(self, event: Union[types.Message, types.CallbackQuery], session: AsyncSession) -> bool:
        try:
            channels = await orm_get_channels()
        except Exception as e:
            print(f"ORM channels: {e}")
            return False

        # Проверяем подписку на каждый канал
        for channel in channels:
            try:
                member = await event.bot.get_chat_member(chat_id=channel["channel_id"], user_id=event.from_user.id)

                req = await orm_check_user_request(session, chat_id=channel["channel_id"], user_id=event.from_user.id)
                if req is True:
                    continue

                if member.status in ["left", "kicked", "restricted"]:
                    return False


            except Exception as e:
                print(f"Ошибка при проверке подписки: {e}")
                return False

        return True





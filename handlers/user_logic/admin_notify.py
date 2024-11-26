from aiogram.types import Message, InlineKeyboardMarkup
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import HelpMessage
from database.orm_query import orm_get_admins
from kbds.kbs import admin_new_btns


async def admin_notify_help(message: Message, session: AsyncSession, help_mess: HelpMessage):
    admins_list = await orm_get_admins(session)
    print(admins_list)
    text = (
        f"📩 <b>Новая заявка в поддержку</b>\n"
        f"Создал: @{message.from_user.username} | {message.from_user.id}\n\n"
        f"Сообщение: {message.text}"
    )
 
    for admin in admins_list:
        await message.bot.send_message(
            chat_id=admin,
            text=text,
            reply_markup=await admin_new_btns(help_mess)
        )


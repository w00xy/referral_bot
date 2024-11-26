from typing import Union

from aiogram import types

from config import BOT_NAME, FAKE_BIDS
from database.models import UserHistory


async def linkify(user_id):
    return f"https://t.me/{BOT_NAME}?start={user_id}"


def truncate_text(text: str, max_length: int = 30) -> str:
    try:
        if len(text) > max_length:
            return text[:max_length].rstrip() + "..." #rstrip removes trailing whitespace
        else:
            return text
    except TypeError:
        return "(Error: Invalid input)" # Handle cases where input is not a string

async def send_check_user(event: Union[types.Message, types.CallbackQuery], bid: UserHistory, check: str):
    text = (
        f"✅<b> Успешный вывод</b>\n\n"
        f"<b>Ответ от Администратора:</b>\n{check}\n\n"
        f"<b>Заявка номер:</b><b><i> {bid.id + FAKE_BIDS}</i></b>\n"
        f"<b>Сумма:</b> <b><i>{bid.amount} USDT</i></b>"
    )

    await event.bot.send_message(
        chat_id=bid.user_id,
        text=text
    )

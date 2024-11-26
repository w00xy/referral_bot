from typing import Union

from aiogram import types
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User
from database.orm_query import orm_add_user, orm_verify_referral, orm_get_referer, add_money
from kbds.kbs import get_channels_btns
from utils.texts import get_not_ref_reg_text, get_ref_reg_text


async def handle_new_user(
        event: Union[types.Message, types.CallbackQuery],
        session: AsyncSession,
        state: FSMContext,
        user_id: int,
        first_name: str,
        referer_id: str = None):
    if isinstance(event, types.Message):
        message = event
    elif isinstance(event, types.CallbackQuery):
        message = event.message
    else:
        print(f"Не является Message или CallbackQuery handle_new_user")
        return

    try:
        referer_id = int(referer_id)
        if message.from_user.id == referer_id:
            await message.answer(
                text='*Ты достаточно умен, нашел свою реферальную ссылку, но приглашать нужно друзей!*',
                parse_mode=ParseMode.MARKDOWN
            )
            referer_id = None
            return
    except Exception as ex:
        referer_id = None
        print(f"No referer id - {ex}")

    try:
        await orm_add_user(session, user_id, message.from_user.username, referer_id, first_name)
    except Exception as ex:
        print(f"Error orm_add_user: {ex}")

    if referer_id:
        # ответ текстом, что друг прислал деньги
        await message.answer(
            text=await get_ref_reg_text(),
            reply_markup=await get_channels_btns(),
        )
        return

    await message.answer(
        text=await get_not_ref_reg_text(),
        reply_markup=await get_channels_btns(),
    )

async def verify_user(event: Union[types.Message, types.CallbackQuery], session: AsyncSession, user: User):
    user_id = event.from_user.id
    print(f"verify_user: {user_id}\n\n")
    try:
        print(f"verify_user try to update status and add money")
        if user.referral.referer_id and user.referral.is_verified == False:
            print("verify_user условие прошло")
            # добавляем после проверки
            try:
                await orm_verify_referral(session, user_id)
            except Exception as ex:
                print(f"Error orm_verify_referral: {ex}")
            # добавляем деньги только после всех подписок
            try:
                await add_money(user_id=user.referral.referer_id, session=session)
            except Exception as ex:
                print(f"Error add_money referer: {ex}")
            try:
                await add_money(user_id=user_id, session=session)
            except Exception as ex:
                print(f"Error add_money user: {ex}")
            # Тестово
            # await message.answer(
            #     text="Реферал подвержден",
            # )
            return
    except Exception as ex:
        print(f"Error verify_user: {ex}")

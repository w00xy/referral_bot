import random

from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from kbds.kbs import *
from kbds.kbs import home_button
from states.user_states import UserStates
from utils.texts import *
from utils.texts import traffic_text

fake_traffic_router = Router()

# def generate_fake_users(num_users=5000, max_referrals_per_user=800):
#     """Генерирует случайные данные, контролируя общую сумму рефералов."""

@fake_traffic_router.callback_query(F.data == "get_traffic")
async def handle_traffic_bot(call: types.CallbackQuery, session: AsyncSession, state: FSMContext):
    await call.answer()

    await call.message.edit_text(
        text=await traffic_text(),
        reply_markup=home_button
    )

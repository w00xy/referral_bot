from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, ChatJoinRequest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.util import merge_lists_w_ordering

from database.orm_query import *
from filters.chat_types import IsSubscribedFilter, ChatTypeFilter
from handlers.start.new_user import handle_new_user
from kbds.kbs import *
from utils.texts import *

join_requests_router = Router()

@join_requests_router.chat_join_request()
async def join_request_handle(request: ChatJoinRequest, session: AsyncSession):
    try:
        print(f"Пробуем добавить заявку, {request.from_user.id}")
        # Получаем ID группы, в которую подана заявка
        group_id = request.chat.id

        # Получаем ID пользователя, подавшего заявку
        user_id = request.from_user.id
        try:
            await orm_add_user_request(session, user_id, group_id)
        except Exception as e:
            print(f"Error join_req_handle orm_add_user_req - {e}")
            
    except Exception as e:
        print(f"Error join_req_handle - {e}")



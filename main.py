import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommandScopeAllPrivateChats

from config import BOT_TOKEN
from database.engine import create_db, drop_db, session_maker
from handlers import routers
from middlewares.db import DataBaseSession
from utils.bot_commands import command_list


# creating database
async def on_startup():

    run_param = False
    if run_param:
        await drop_db()

    # Делегировано алембику
    await create_db()


async def on_shutdown():
    print('Бот упал')


async def main():

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher()

    # on_start_up and shotdown functions
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # drop offline messages
    await bot.delete_webhook(drop_pending_updates=True)

    # подключение роутеров
    for router in routers:
        dp.include_router(router)

    # connecting the middlewares
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    # кнопки из меню справа снизу
    await bot.set_my_commands(commands=command_list, scope=BotCommandScopeAllPrivateChats())

    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exit')

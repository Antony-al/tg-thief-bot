import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config_reader import config
from handlers import cmd_handlers, txt_handlers, handlers_func, callback_handlers
import db_actions



async def main():
    BOT_TOKEN = config.bot_token.get_secret_value()
    bot = Bot(token=BOT_TOKEN)
    db = db_actions.MemeStealerDb()
    db.create_db()
    db.close()
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    dp.include_router(cmd_handlers.router)
    """
    Пока не надо.
    dp.include_router(txt_handlers.router)
    dp.include_router(handlers_func.router)
    dp.include_router(callback_handlers.router)
    """
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
    
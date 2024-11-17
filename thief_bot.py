import json
import asyncio
from telethon import TelegramClient
from aiogram import Bot, Dispatcher, Router
from config import api_id, api_hash, bot_token
from functions.all_functions import setup_database, periodic_fetch_and_review
from handlers import callback_handlers, cmd_handlers

# Загрузка конфигурации
with open("config.json", "r") as f:
    config = json.load(f)

api_id = config["api_id"]
api_hash = config["api_hash"]
bot_token = config["bot_token"]

client = TelegramClient('meme_user', api_id, api_hash, 
                        device_model = "iPhone 13 Pro Max",
                        system_version = "14.8.1",
                        app_version = "8.4",
                        lang_code = "en",
                        system_lang_code = "en-US")
bot = Bot(token=bot_token)
dp = Dispatcher()
message_router = Router()
callback_router = Router()

async def main():
    # Настройка базы данных
    await setup_database()

    # Регистрация роутеров
    dp.include_router(cmd_handlers.router)
    dp.include_router(callback_handlers.router)
    callback_handlers.set_bot(bot)

    # Асинхронное использование клиента Telethon
    async with client:
        # Запуск периодической проверки
        asyncio.create_task(periodic_fetch_and_review(client))

        # Запуск long-polling для бота
        print("Бот запущен...")
        await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот остановлен.")

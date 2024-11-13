
import json, asyncio
from telethon import TelegramClient
from aiogram import Bot, Dispatcher, F, Router
from config import api_id, api_hash, bot_token, review_chat_id, channels_to_monitor, my_channel, my_channel_id, db_name, ad_keywords, link_pattern
from functions.all_functions import setup_database, periodic_fetch_and_review
from handlers import callback_handlers, cmd_handlers

with open("config.json", "r") as f:
    config = json.load(f)

api_id = config["api_id"]
api_hash = config["api_hash"]
bot_token = config["bot_token"]
review_chat_id = config["review_chat_id"]  # Ваш личный ID чата для проверки
client = TelegramClient('meme_user', api_id, api_hash)
bot = Bot(token=bot_token)
dp = Dispatcher()
message_router = Router()
callback_router = Router()
channels_to_monitor = config["channels_to_monitor"]
my_channel = config["my_channel"]
my_channel_id = config["my_channel_id"]



async def main():
    await setup_database()
    dp.include_router(cmd_handlers.router)
    dp.include_router(callback_handlers.router)
    callback_handlers.set_bot(bot)
    asyncio.create_task(periodic_fetch_and_review())  # Запускаем цикл проверки каналов
    await dp.start_polling(bot)

# Запуск основного процесса
print("Бот запущен...")
with client:
    client.loop.run_until_complete(main())

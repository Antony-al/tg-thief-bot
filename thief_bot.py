import aiosqlite
import json
import asyncio
import re
import io
import os
from telethon import TelegramClient
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.filters import Command
from aiogram.filters.callback_data import CallbackData
from aiogram import F
from aiogram import Router
from aiogram.types.input_file import FSInputFile

# Загружаем конфигурацию из config.json
with open("config.json", "r") as f:
    config = json.load(f)

# Параметры для Telegram API
api_id = config["api_id"]
api_hash = config["api_hash"]
bot_token = config["bot_token"]
review_chat_id = config["review_chat_id"]  # Ваш личный ID чата для проверки

# Инициализация клиентов
client = TelegramClient('meme_user', api_id, api_hash)
bot = Bot(token=bot_token)
dp = Dispatcher()

# Создаем роутеры для сообщений и callback-запросов
message_router = Router()
callback_router = Router()

# Каналы для мониторинга и ваш канал
channels_to_monitor = config["channels_to_monitor"]
my_channel = config["my_channel"]
my_channel_id = config["my_channel_id"]

# Имя файла базы данных
db_name = 'meme_bot.db'

# Ключевые слова, по которым определяются рекламные посты
ad_keywords = ["реклама", "спонсор", "поддержи", "подписывайся", "партнёрская", "промо"]
link_pattern = re.compile(r"(t\.me/|@|https?://)")

class MemeActionCallback(CallbackData, prefix="meme"):
    action: str
    from_channel_id: str
    channel_id: str
    message_id: int

async def setup_database():
    """Создаем таблицу для хранения ID сообщений, если ее еще нет"""
    async with aiosqlite.connect(db_name) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                channel_id TEXT,
                message_id INTEGER,
                PRIMARY KEY (channel_id, message_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS queue (
                channel_id TEXT,
                message_id INTEGER,
                media_path TEXT,
                caption TEXT,
                PRIMARY KEY (channel_id, message_id)
            )
        """)
        await db.commit()

async def is_posted(channel_id, message_id):
    """Проверяем, было ли сообщение уже опубликовано"""
    async with aiosqlite.connect(db_name) as db:
        async with db.execute("SELECT 1 FROM posts WHERE channel_id = ? AND message_id = ?", 
                              (channel_id, message_id)) as cursor:
            return await cursor.fetchone() is not None

async def mark_as_posted(channel_id, message_id):
    """Помечаем сообщение как опубликованное, записывая его ID в базу данных"""
    async with aiosqlite.connect(db_name) as db:
        await db.execute("INSERT INTO posts (channel_id, message_id) VALUES (?, ?)", 
                         (channel_id, message_id))
        await db.commit()

async def add_to_queue(channel_id, message_id, media_path, caption):
    async with aiosqlite.connect(db_name) as db:
        await db.execute("INSERT OR IGNORE INTO queue (channel_id, message_id, media_path, caption) VALUES (?, ?, ?, ?)",
                         (channel_id, message_id, media_path, caption))
        await db.commit()

# Функции для проверки на признаки рекламы
def is_advertisement(message):
    """Проверка, является ли пост рекламным"""
    text = message.text or ""
    # Проверка на ключевые слова
    if any(keyword in text.lower() for keyword in ad_keywords):
        return True
    # Проверка на наличие ссылок
    if contains_external_links(text):
        return True
    # Проверка на форварды
    if is_forwarded(message):
        return True
    return False

def contains_external_links(text):
    """Проверка на наличие внешних ссылок или упоминаний"""
    return bool(link_pattern.search(text))

def is_forwarded(message):
    """Проверка, является ли сообщение пересланным"""
    return message.fwd_from is not None

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    await message.answer("Привет! Этот бот проверяет и публикует мемы. Используйте команды для управления.")

# Функция для создания правильной клавиатуры
def create_approve_reject_keyboard(from_channel_id, message_id):
    # Преобразуем channel_id в строку, если это необходимо
    my_channel_id_str = str(my_channel_id)
    print("my_channel_id_str", my_channel_id_str)
    print("from_channel_id", from_channel_id)
    approve_callback = MemeActionCallback(action="approve", from_channel_id=str(from_channel_id), channel_id=my_channel_id_str, message_id=message_id).pack()
    reject_callback = MemeActionCallback(action="reject", from_channel_id=str(from_channel_id), channel_id=my_channel_id_str, message_id=message_id).pack()

    approve_button = InlineKeyboardButton(text="Запостить", callback_data=approve_callback)
    reject_button = InlineKeyboardButton(text="Отклонить", callback_data=reject_callback)
    return InlineKeyboardMarkup(inline_keyboard=[[approve_button, reject_button]])

# Обновленный метод для отправки сообщений с клавишами
async def send_review_message(chat_id, media_path, caption, from_channel_id, message_id):
    print("Before create_approve_reject_keyboard")
    markup = create_approve_reject_keyboard(from_channel_id, message_id)
    print("After create_approve_reject_keyboard")
    
    if media_path:
        print("Media_path: ", media_path)
        file_name = os.path.basename(media_path)
        file = FSInputFile(media_path)  # Просто указываем путь к файлу
        await bot.send_document(chat_id, file, caption=caption, reply_markup=markup)
    # else:
        # file = InputFile(media_path)
        # await bot.send_document(chat_id, open(media_path, 'rb'), caption=caption, reply_markup=markup)
        # with open(media_path, 'rb') as file:
        #     # Читаем файл в память
        #     file_data = io.BytesIO(file.read())
        #     # Получаем имя файла из пути
        #     file_name = os.path.basename(media_path)
        #     # Создаем объект InputFile из данных в памяти
        #     file_input = InputFile(file_data, filename=file_name)  # Используем имя файла
        #     await bot.send_document(chat_id, file_input, caption=caption, reply_markup=markup)
    else:
        await bot.send_message(chat_id, caption, reply_markup=markup)

@dp.callback_query(MemeActionCallback.filter())
async def process_callback(callback_query: types.CallbackQuery, callback_data: MemeActionCallback):
    action = callback_data.action
    channel_id = callback_data.from_channel_id
    message_id = callback_data.message_id

    if action == 'approve':
        async with aiosqlite.connect(db_name) as db:
            async with db.execute("SELECT media_path, caption FROM queue WHERE channel_id = ? AND message_id = ?", 
                                  (channel_id, message_id)) as cursor:
                result = await cursor.fetchone()
                if result:
                    media_path, caption = result
                    file = FSInputFile(media_path)
                    await bot.send_document(my_channel, file, caption=caption)
                    await mark_as_posted(channel_id, message_id)
                    await db.execute("DELETE FROM queue WHERE channel_id = ? AND message_id = ?", (channel_id, message_id))
                    await db.commit()
                    await bot.answer_callback_query(callback_query.id, "Пост опубликован.")
                    await asyncio.sleep(15 * 60)  # Задержка 15 минут
    elif action == 'reject':
        # Удаляем сообщение из чата, в котором оно было отправлено
        try:
            await bot.delete_message(review_chat_id, callback_query.message.message_id)
            print(f"Сообщение {message_id} из чата {review_chat_id} удалено.")
        except Exception as e:
            print(f"Ошибка при удалении сообщения: {e}")
        async with aiosqlite.connect(db_name) as db:
            await db.execute("DELETE FROM queue WHERE channel_id = ? AND message_id = ?", (channel_id, message_id))
            await db.commit()
            await bot.answer_callback_query(callback_query.id, "Пост отклонен.")

async def fetch_and_review():
    print("Начало выполнения fetch_and_post()")
    posts_to_post = []  # Список для хранения сообщений, которые нужно опубликовать

    # Сбор сообщений, подходящих для постинга
    for channel in channels_to_monitor:
        print("Обрабатываем канал:", channel)
        try:
            async for message in client.iter_messages(channel, limit=5):
                channel_id = str(message.chat_id)  # Уникальный идентификатор канала
                if await is_posted(channel_id, message.id):  # Проверяем, было ли сообщение уже опубликовано
                    print(f"Сообщение {message.id} из канала {channel_id} уже опубликовано, пропускаем.")
                    continue

                # Проверка на рекламу
                if is_advertisement(message):
                    print(f"Сообщение {message.id} из канала {channel_id} определено как реклама, пропускаем.")
                    continue

                media_path = await message.download_media() if message.media else None
                await add_to_queue(str(message.chat_id), message.id, media_path, message.text)

                print("Before send_review_message")
                await send_review_message(review_chat_id, media_path, message.text, channel_id, message.id)
                print("After send_review_message")
                # Создаем клавиши для "Запостить" и "Отклонить"
                # markup = create_approve_reject_keyboard(message.chat_id, message.id)

                # # Отправляем сообщение с кнопками на ваш ID
                # if media_path:
                #     await bot.send_document(review_chat_id, open(media_path, 'rb'), caption=message.text, reply_markup=markup)
                # else:
                #     await bot.send_message(review_chat_id, message.text, reply_markup=markup)

        except Exception as e:
            print(f"Ошибка при обработке канала {channel}: {e}")

# Продолжение функции для публикации сообщений с задержкой
async def periodic_fetch_and_review():
    while True:
        await fetch_and_review()
        print("Завершена проверка каналов. Следующая проверка через 1 час.")
        await asyncio.sleep(3600)  # Задержка в 1 час

async def main():
    await setup_database()
    dp.include_router(message_router)  # Регистрируем маршрутизатор сообщений
    dp.include_router(callback_router)  # Регистрируем маршрутизатор callback
    asyncio.create_task(periodic_fetch_and_review())  # Запускаем цикл проверки каналов
    await dp.start_polling(bot)

# Запуск основного процесса
print("Бот запущен...")
with client:
    client.loop.run_until_complete(main())

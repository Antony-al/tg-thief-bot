import aiosqlite, os, asyncio
from aiogram.types.input_file import FSInputFile
from handlers.callback_handlers import MemeActionCallback
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile

from config import api_id, api_hash, bot_token, review_chat_id, channels_to_monitor, my_channel, my_channel_id, db_name, ad_keywords, link_pattern

bot = None

def set_bot(instance):
    global bot
    bot = instance



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


async def fetch_and_review(client):
    from thief_bot import client
    print("Начало выполнения fetch_and_post()")
    posts_to_post = []  # Список для хранения сообщений, которые нужно опубликовать

    if not client.is_connected():
        print("Клиент не подключен. Попытка подключиться...")
        await client.connect()

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
async def periodic_fetch_and_review(client):
    while True:
        await fetch_and_review(client)
        print("Завершена проверка каналов. Следующая проверка через 1 час.")
        await asyncio.sleep(3600)  # Задержка в 1 час

async def is_posted(channel_id, message_id):
    """Проверяем, было ли сообщение уже опубликовано"""
    async with aiosqlite.connect(db_name) as db:
        async with db.execute("SELECT 1 FROM posts WHERE channel_id = ? AND message_id = ?", 
                              (channel_id, message_id)) as cursor:
            return await cursor.fetchone() is not None


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

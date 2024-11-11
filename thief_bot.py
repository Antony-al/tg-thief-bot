import aiosqlite
import json
import asyncio
from telethon import TelegramClient

# Загружаем конфигурацию из config.json
with open("config.json", "r") as f:
    config = json.load(f)

# Параметры для Telegram API
api_id = config["api_id"]
api_hash = config["api_hash"]

# Подключаемся к Telegram как пользователь, без bot_token
client = TelegramClient('meme_user', api_id, api_hash)

# Каналы для мониторинга и ваш канал
channels_to_monitor = config["channels_to_monitor"]
my_channel = config["my_channel"]

# Имя файла базы данных
db_name = 'meme_bot.db'

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

async def fetch_and_post():
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

                # Проверяем количество просмотров и пересылок
                views = message.views or 0
                forwards = message.forwards or 0

                print(f"Пост на канале {channel} - Просмотры: {views}, Пересылки: {forwards}")

                # Фильтрация на основе критериев
                if views > 1000 and forwards > 10:
                    # Скачивание медиа, если оно есть
                    if message.media:
                        path = await message.download_media()
                        posts_to_post.append((channel_id, message.id, path, message.text))  # Добавляем ID канала, ID сообщения, медиа и текст
                        print("Медиа добавлено для отложенного постинга:", path)
                    else:
                        posts_to_post.append((channel_id, message.id, None, message.text))  # Только текст
                        print("Текст добавлен для отложенного постинга.")

        except Exception as e:
            print(f"Ошибка при обработке канала {channel}: {e}")

    # Публикация сообщений с 15-минутной задержкой
    for channel_id, message_id, path, text in posts_to_post:
        if path:
            await client.send_file(my_channel, path, caption=text)
            print("Отправлено в канал с медиа.")
        else:
            await client.send_message(my_channel, text)
            print("Отправлено в канал с текстом.")

        # Помечаем сообщение как опубликованное
        await mark_as_posted(channel_id, message_id)

        # Задержка в 15 минут перед следующим постом
        await asyncio.sleep(15 * 60)  # 15 минут = 15 * 60 секунд

async def main():
    await setup_database()  # Настройка базы данных
    while True:
        await fetch_and_post()  # Запускаем задачу
        print("Ожидание перед следующим запуском fetch_and_post...")
        await asyncio.sleep(3600)  # Ожидание 1 часа перед следующим циклом сбора

# Запуск основного процесса
print("Бот запущен...")
with client:
    client.loop.run_until_complete(main())

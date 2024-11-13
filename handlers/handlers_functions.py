import aiosqlite
from config import db_name

async def mark_as_posted(channel_id, message_id):
    """Помечаем сообщение как опубликованное, записывая его ID в базу данных"""
    async with aiosqlite.connect(db_name) as db:
        await db.execute("INSERT INTO posts (channel_id, message_id) VALUES (?, ?)", 
                         (channel_id, message_id))
        await db.commit()
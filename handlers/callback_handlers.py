import aiosqlite, asyncio
from aiogram import Router, types
from config import db_name
from aiogram.filters.callback_data import CallbackData
from aiogram.types.input_file import FSInputFile
from config import my_channel, review_chat_id
from handlers.handlers_functions import mark_as_posted

router = Router()

bot = None

def set_bot(instance):
    global bot
    bot = instance

class MemeActionCallback(CallbackData, prefix="meme"):
    action: str
    from_channel_id: str
    channel_id: str
    message_id: int    

@router.callback_query(MemeActionCallback.filter())
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

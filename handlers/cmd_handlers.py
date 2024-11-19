from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
import db_actions
import handlers.hadlers_reply as reply

router = Router()

@router.message(Command("start")) 
async def cmd_start(message: Message):
    db = db_actions.MemeStealerDb()
    if not db.user_exists(message.from_user.id):
        db.add_user(message.from_user.id)
        db.close()
    else: db.close()    
    await message.answer(reply.start_reply())

# загрузить мемы из указанных каналов
@router.message(Command("getmemes")) 
async def get_memes(message: Message):
    pass

""""
api_hash, bot_token, my_channel, my_channel_id
    """
@router.message(Command("settings")) 
async def set_settings(message: Message):
    pass
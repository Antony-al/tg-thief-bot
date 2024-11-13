from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()
bot = None

def set_bot(instance):
    global bot
    bot = instance


@router.message(Command("start"))
async def send_welcome(message: Message):
    await message.answer("Привет! Этот бот проверяет и публикует мемы. Используйте команды для управления.")
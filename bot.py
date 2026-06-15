import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

# 1. Настройка логирования: теперь все ошибки будут видны в консоли
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Твой токен
TOKEN = "8877027563:AAER5zuqzfpzHZESBvj_Qd44sUkSCQT4kjI"

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    logger.info(f"Получена команда /start от пользователя {message.from_user.id}")
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🎮 Играть",
        web_app=WebAppInfo(url="https://stars-droper-main.vercel.app/")
    ))
    builder.add(InlineKeyboardButton(text="📢 Канал", url="https://t.me/nowear_FREE"))
    builder.adjust(1)

    text = "👋 Привет! Нажми кнопку ниже, чтобы войти в игру:"
    await message.answer(text, reply_markup=builder.as_markup())
    logger.info("Ответ отправлен")

async def main():
    logger.info("Запуск бота...")
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")

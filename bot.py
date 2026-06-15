import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Настройка логирования, чтобы видеть ошибки
logging.basicConfig(level=logging.INFO)

# Твой токен
bot = Bot(token="8877027563:AAER5zuqzfpzHZESBvj_Qd44sUkSCQT4kjI")
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Играть"
    builder.add(InlineKeyboardButton(
        text="🎮 Играть",
        web_app=WebAppInfo(url="https://stars-droper-main.vercel.app/")
    ))
    
    # Кнопка "Канал"
    builder.add(InlineKeyboardButton(
        text="📢 Канал", 
        url="https://t.me/nowear_FREE"
    ))
    
    builder.adjust(1) 

    # Текст с обычными эмодзи (они всегда работают)
    text = (
        f"👋 <b>Привет, {message.from_user.first_name}!</b>\n\n"
        f"💪 <b>Добро пожаловать в NowearSpin!</b>\n\n"
        f"🏆 <b>NowearSpin: здесь не играют по правилам, здесь их создают. "
        f"Кейсы, колесо удачи, апгрейды — всё, что нужно для большого выигрыша, собрано в одном месте.\n"
        f"Докажи, что ты лучший. Твой джекпот уже ждет тебя!</b>\n\n"
        f"👇 <b>Нажми «Играть», чтобы открыть приложение!</b>"
    )

    await message.answer(text, parse_mode="html", reply_markup=builder.as_markup())

async def main():
    print("Бот успешно запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

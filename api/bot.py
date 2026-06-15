from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, WebAppInfo, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

# Вставь свой токен
bot = Bot(token="8877027563:AAER5zuqzfpzHZESBvj_Qd44sUkSCQT4kjI")
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    builder = InlineKeyboardBuilder()
    
    # Кнопка "Играть" с WebApp
    builder.add(InlineKeyboardButton(
        text="Играть",
        web_app=WebAppInfo(url="https://stars-droper-main.vercel.app/") # Укажи ссылку на хостинг
    ))
    
    # Кнопка "Канал"
    builder.add(InlineKeyboardButton(
        text="Канал", 
        url="https://t.me/nowear_FREE"
    ))
    
    builder.adjust(1) # Это должно быть внутри функции

    # Текст приветствия
    text = (
        f'<tg-emoji emoji-id="5472055112702629499">👋</tg-emoji> <b>Привет, {message.from_user.first_name}!</b>\n\n'
        f'<tg-emoji emoji-id="5471883477219549006">💪</tg-emoji> <b>Добро пожаловать в NowearSpin!</b>\n\n'
        f'<tg-emoji emoji-id="5280769763398671636">🏆</tg-emoji> <b>NowearSpin: здесь не играют по правилам, здесь их создают. '
        f'Кейсы, колесо удачи, апгрейды — всё, что нужно для большого выигрыша, собрано в одном месте.\n'
        f'Докажи, что ты лучший. Твой джекпот уже ждет тебя!</b>\n\n'
        f'<tg-emoji emoji-id="5470177992950946662">👇</tg-emoji> <b>Нажми играть чтобы открыть приложение!</b>'
    )

    await message.answer(text, parse_mode="html", reply_markup=builder.as_markup())

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

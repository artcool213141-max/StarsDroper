from aiogram import Bot, Dispatcher, F 
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, WebAppInfo, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
import asyncio

bot = Bot(token="Т8877027563:AAER5zuqzfpzHZESBvj_Qd44sUkSCQT4kjI")
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Играть",
      web_app=WebAppInfo(url="пупу", icon_emoji_id="5467583879948803288") # Ссылка на ваш сайт
    ))
    builder.add(InlineKeyboardButton(text="Канал", url="https://t.me/nowear_FREE", icon_emoji_id="5431376038628171216"))
builder.adjust(1)

await message.answer(
f'<tg-emoji emoji-id="5472055112702629499">👋</tg-emoji> <b>Привет, {message.from_user.first_name}!</b>\n'
f'<tg-emoji emoji-id="5471883477219549006">💪</tg-emoji> <b>Добро пожаловать в NowearSpin! </b>\n'
f'<tg-emoji emoji-id="5280769763398671636">🏆</tg-emoji> <b>NowearSpin: здесь не играют по правилам, здесь их создают. Кейсы, колесо удачи, апгрейды — всё, что нужно для большого выиграша, собрано в одном месте.
Докажи, что ты лучший. Твой джекпот уже ждет тебя!</b>\n'
f'<tg-emoji emoji-id="5470177992950946662">👇</tg-emoji> <b>Нажми играть чтобы открыть приложение!</b>', parse_mode="html", reply_markup=builder.as_markup())

async def main():
   await dp.start_polling(bot)

if __name__ == "__main__":
   asyncio.run(main())

import asyncio
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, WebAppInfo, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Токен лучше брать из переменной окружения, но для начала сойдет и так
bot = Bot(token="8877027563:AAER5zuqzfpzHZESBvj_Qd44sUkSCQT4kjI")
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: Message):
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="Играть",
        web_app=WebAppInfo(url="ТВОЯ_ССЫЛКА_НА_САЙТ", icon_emoji_id="5467583879948803288")
    ))
    builder.add(InlineKeyboardButton(text="Канал", url="https://t.me/nowear_FREE", icon_emoji_id="5431376038628171216"))
    builder.adjust(1)

    # Используем тройные кавычки для многострочного текста
    text = f"""<tg-emoji emoji-id="5472055112702629499">👋</tg-emoji> <b>Привет, {message.from_user.first_name}!</b>
<tg-emoji emoji-id="5471883477219549006">💪</tg-emoji> <b>Добро пожаловать в NowearSpin!</b>
<tg-emoji emoji-id="5280769763398671636">🏆</tg-emoji> <b>NowearSpin: здесь не играют по правилам, здесь их создают. Кейсы, колесо удачи, апгрейды — всё, что нужно для большого выиграша, собрано в одном месте.
Докажи, что ты лучший. Твой джекпот уже ждет тебя!</b>
<tg-emoji emoji-id="5470177992950946662">👇</tg-emoji> <b>Нажми играть чтобы открыть приложение!</b>"""
    
    await message.answer(text, parse_mode="html", reply_markup=builder.as_markup())

async def main():
    # Добавь вот эти две строчки:
    await bot.delete_webhook(drop_pending_updates=True)
    print("--- ВЕБХУК УДАЛЕН, ЗАПУСКАЮ POLLING ---")
    
    await dp.start_polling(bot)

# Этот блок тут нужен, чтобы файл можно было импортировать в index.py
if __name__ == "__main__":
    asyncio.run(main())

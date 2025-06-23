from config_data.config import load_config
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards import start_menu
from handlers import keyboard_handler


# Загружаем конфиг в переменную
config = load_config('.env')
bot_token = config.tg_bot.token
BOT_TOKEN = bot_token


# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

start_keyboard = start_menu.start_menu_keyboard_trail()


# Этот хэндлер будет срабатывать на команду "/delmenu"
# и удалять кнопку Menu c командами

@dp.message(CommandStart())
async def process_start_command(message: Message):
    await message.answer(
        text='Добро пожаловать!',
        reply_markup=start_keyboard
    )

dp.include_router(keyboard_handler.router)


# Запускаем поллинг
if __name__ == '__main__':
    try:
        print('Бот запущен!')
        dp.run_polling(bot)
    except KeyboardInterrupt:
        print('Бот остановлен!')

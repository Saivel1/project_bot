import datetime
from config_data.config import load_config
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from keyboards import start_menu
from handlers import keyboard_handler
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from status.status_keys import get_message_by_status
from handlers.keyboard_handler import get_user_data, update_user_field
from datetime import datetime
from marzban.Backend import MarzbanBackendContext



# Загружаем конфиг в переменную
config = load_config('.env')
bot_token = config.tg_bot.token
BOT_TOKEN = bot_token


# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# Этот хэндлер будет срабатывать на команду "/delmenu"
# и удалять кнопку Menu c командами

@dp.message(CommandStart())
async def process_start_command(message: Message, state: FSMContext):
    user_data = await get_user_data(state)
    message_text = get_message_by_status('start_menu', user_data.trial, user_data.subscription_end)
    async with MarzbanBackendContext() as backend:
        res = await backend.get_user(str(message.from_user.id))
        if res:
            res = res['subscription_url']
            await update_user_field(state, link=res)
        else:
            res = await backend.create_user(str(message.from_user.id))
            res = res['subscription_url']
            await update_user_field(state, link=res)

    await message.answer(
        text=message_text['text'],
        reply_markup=message_text['keyboard']
    )




dp.include_router(keyboard_handler.router)


# Запускаем поллинг
if __name__ == '__main__':
    try:
        print('Бот запущен!')
        dp.run_polling(bot)
    except KeyboardInterrupt:
        print('Бот остановлен!')

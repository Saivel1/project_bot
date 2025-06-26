from config_data.config import load_config
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart, CommandObject
from refferal.refferal_logic import safe_add_referral
from aiogram.types import Message
from handlers import keyboard_handler
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from status.status_keys import get_message_by_status
from handlers.keyboard_handler import get_user_data, update_user_field



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
async def process_start_command(message: Message, state: FSMContext, command: CommandObject):
    user_data = await get_user_data(state)
    message_text = get_message_by_status('start_menu', user_data.trial, user_data.subscription_end)
    ref_id = command.args

    if ref_id and not user_data.first_visit_completed:
        try:
            ref_id = int(ref_id)
            user_id = int(message.from_user.id)
            if ref_id == user_id:
                raise ValueError
            await safe_add_referral(user_id, ref_id)
        except ValueError as e:
            print(f"Ошибка при добавлении реферальной связи: {e}")

    if not user_data.first_visit_completed:
        await update_user_field(state, first_visit_completed=True)


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

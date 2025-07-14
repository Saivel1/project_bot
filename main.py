from config_data.config import load_config
from aiogram import Bot, Dispatcher
from handlers import keyboard_handler
from db.db_inject import db_manager
import asyncio
from redis_bot.redis_main import RedisUserCache
from redis_bot.redis_middleware import RedisMiddleware
from status.block_middleware import UserBlockedMiddleware, UserUnblockedMiddleware
from messages.sub_reminder import check_and_send_subscription_reminders


# Загружаем конфиг в переменную
config = load_config('.env')
bot_token = config.tg_bot.token
BOT_TOKEN = bot_token

# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def on_startup():
    """ТОЛЬКО инициализация БД и Redis"""
    await db_manager.initialize_connection_pool()
    await db_manager.create_tables()

    global redis_cache_instance  # Сохраним в глобальную переменную
    redis_cache_instance = RedisUserCache()
    await redis_cache_instance.connect()

    dp.message.middleware(UserUnblockedMiddleware())
    dp.callback_query.middleware(UserUnblockedMiddleware())

    # Регистрируем middleware для обработки ошибок блокировки
    dp.errors.middleware(UserBlockedMiddleware())



async def on_shutdown():
    """Очистка при остановке бота"""
    await db_manager.close_pool()
    global redis_cache_instance
    if redis_cache_instance:
        await redis_cache_instance.disconnect()

# Этот хэндлер будет срабатывать на команду "/delmenu"
# и удалять кнопку Menu c командами

async def main():
    # Регистрируем startup/shutdown
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # РЕГИСТРИРУЕМ MIDDLEWARE ЗДЕСЬ, ПОСЛЕ startup
    await on_startup()  # Сначала инициализируем Redis
    # Теперь регистрируем middleware с уже подключенным Redis
    dp.callback_query.middleware(RedisMiddleware(redis_cache_instance))
    dp.message.middleware(RedisMiddleware(redis_cache_instance))

    asyncio.create_task(check_and_send_subscription_reminders(bot))
    dp.include_router(keyboard_handler.router)
    dp.include_router(keyboard_handler.admin_router)

    await dp.start_polling(bot)


# Запускаем поллинг
if __name__ == '__main__':
    try:
        print('Бот запущен!')
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Бот остановлен!')

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
import logging

class RedisMiddleware(BaseMiddleware):
    def __init__(self, redis_cache):
        self.redis_cache = redis_cache

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        # Проверяем соединение
        if self.redis_cache and self.redis_cache.redis_client:
            try:
                await self.redis_cache.redis_client.ping()
            except Exception as e:
                print(f"Middleware: PING ошибка: {e}")
                # Пытаемся переподключиться
                try:
                    await self.redis_cache.connect()
                except Exception as reconnect_error:
                    print(f"Middleware: Ошибка переподключения: {reconnect_error}")

        data['redis_cache'] = self.redis_cache
        return await handler(event, data)
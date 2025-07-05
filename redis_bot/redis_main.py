import redis.asyncio as redis
import json
import logging
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import time

@dataclass(slots=True, frozen=True)
class UserCache:
    """Минимальные данные пользователя для Redis кэша"""
    user_id: int = 0
    balance: int = 0
    subscription_end: int = 0
    trial_end: Optional[int] = None
    trial: str = 'never_used'
    link: Optional[str] = None
    referral_count: int = 0



class RedisUserCache:
    """Класс для работы с кэшем пользователей в Redis"""

    def __init__(self, redis_url: str = "redis://localhost:6379",
                 default_ttl: int = 900):  # 15 минут по умолчанию
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.redis_client: Optional[redis.Redis] = None

    async def __aenter__(self):
        """Вход в контекстный менеджер - подключение к Redis"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Выход из контекстного менеджера - отключение от Redis"""
        await self.disconnect()

    async def connect(self):
        """Подключение к Redis"""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_timeout=30,        # ← Увеличить таймаут
                socket_connect_timeout=10, # ← Увеличить таймаут подключения
                retry_on_timeout=True,    # ← Повторы при таймауте
                health_check_interval=30
            )
            # Проверяем соединение
            await self.redis_client.ping()
            logging.info("Успешное подключение к Redis")
        except Exception as e:
            logging.error(f"Ошибка подключения к Redis: {e}")
            raise

    async def disconnect(self):
        """Отключение от Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logging.info("Соединение с Redis закрыто")

    def _get_user_key(self, user_id: int) -> str:
        """Генерация ключа для пользователя"""
        return f"user_cache:{user_id}"

    async def get_user_cache(self, user_id: int) -> Optional[UserCache]:
        """Получение кэша пользователя из Redis"""
        try:
            key = self._get_user_key(user_id)
            data = await self.redis_client.hgetall(key)

            if not data:
                return None

            # Конвертируем строковые значения в нужные типы
            return UserCache(
                user_id=int(data.get('user_id', 0)),
                balance=int(data.get('balance', 0)),
                subscription_end=int(data.get('subscription_end', 0)),
                trial_end=int(data['trial_end']) if data.get('trial_end') and data['trial_end'] != 'None' else None,
                trial=data.get('trial', 'never_used'),
                link=data.get('link'),
                referral_count=int(data.get('referral_count', 0))
            )

        except Exception as e:
            logging.error(f"Ошибка получения кэша пользователя {user_id}: {e}")
            return None

    async def save_user_cache(self, user_cache: UserCache, ttl: Optional[int] = None) -> bool:
        """Сохранение кэша пользователя в Redis"""
        try:
            key = self._get_user_key(user_cache.user_id)

            redis_data = {
                'user_id': user_cache.user_id,
                'balance': str(user_cache.balance),
                'subscription_end': str(user_cache.subscription_end),
                'trial_end': str(user_cache.trial_end) if user_cache.trial_end is not None else 'None',
                'trial': user_cache.trial,
                'link': user_cache.link,
                'referral_count': str(user_cache.referral_count)
            }

            # Сохраняем данные
            await self.redis_client.hset(key, mapping=redis_data)

            # Устанавливаем TTL
            if ttl or self.default_ttl:
                await self.redis_client.expire(key, ttl or self.default_ttl)

            return True

        except Exception as e:
            logging.error(f"Ошибка сохранения кэша пользователя {user_cache.user_id}: {e}")
            return False

    async def update_user_cache_field(self, user_id: int, ttl: Optional[int] = None, **kwargs) -> Optional[UserCache]:
        """Обновление конкретных полей кэша пользователя"""
        current = await self.get_user_cache(user_id)
        if not current:
            # Если кэша нет, создаем новый с переданными данными
            current = UserCache(user_id=user_id)

        # Создаем обновленный объект
        current_dict = asdict(current)
        current_dict.update(kwargs)
        updated = UserCache(**current_dict)

        success = await self.save_user_cache(updated, ttl)
        return updated if success else None

    async def delete_user_cache(self, user_id: int) -> bool:
        """Удаление кэша пользователя"""
        try:
            key = self._get_user_key(user_id)
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logging.error(f"Ошибка удаления кэша пользователя {user_id}: {e}")
            return False

    async def extend_user_ttl(self, user_id: int, ttl: int) -> bool:
        """Продление времени жизни кэша пользователя"""
        try:
            key = self._get_user_key(user_id)
            return await self.redis_client.expire(key, ttl)
        except Exception as e:
            logging.error(f"Ошибка продления TTL для пользователя {user_id}: {e}")
            return False

    async def is_subscription_active(self, user_id: int) -> bool:
        """Быстрая проверка активности подписки из кэша"""
        cache = await self.get_user_cache(user_id)
        if not cache:
            return False

        current_time = int(time.time())

        # Проверяем пробный период
        if cache.trial == "in_progress" and cache.trial_end and cache.trial_end > current_time:
            return True

        # Проверяем платную подписку
        if cache.subscription_end > current_time:
            return True

        return False


# Простые функции для работы с кэшем в хэндлерах
async def get_user_cache_from_redis(redis_cache: RedisUserCache, user_id: int) -> Optional[UserCache]:
    """Простая функция для получения кэша пользователя в хэндлерах"""
    user_cache = await redis_cache.get_user_cache(user_id)
    if user_cache:
        # Обновляем TTL при каждом обращении
        await redis_cache.extend_user_ttl(user_id, redis_cache.default_ttl)
    return user_cache # Будет пустым, если нет

async def save_user_cache_to_redis(redis_cache: RedisUserCache, user_cache: UserCache) -> bool:
    """Простая функция для сохранения кэша пользователя в хэндлерах"""
    return await redis_cache.save_user_cache(user_cache)

async def update_redis_user_cache_field(redis_cache: RedisUserCache, user_id: int, **kwargs) -> Optional[UserCache]:
    """Простая функция для обновления полей кэша пользователя в хэндлерах"""
    return await redis_cache.update_user_cache_field(user_id, **kwargs)

# Пример инициализации
async def init_redis_cache(redis_url: str = "redis://localhost:6379", ttl: int = 3600):
    """Инициализация Redis кэша"""
    cache = RedisUserCache(redis_url, ttl)
    await cache.connect()
    return cache
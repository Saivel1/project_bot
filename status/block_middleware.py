from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, ErrorEvent
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from typing import Callable, Dict, Any, Awaitable
import logging
from db.db_inject import db_manager as db
from db.db_model import User

logger = logging.getLogger(__name__)

class UserBlockedMiddleware(BaseMiddleware):
   """
   Middleware для обработки случаев блокировки бота пользователем
   """

   async def __call__(
       self,
       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
       event: TelegramObject,
       data: Dict[str, Any]
   ) -> Any:
       try:
           # Выполняем основной хэндлер
           return await handler(event, data)

       except TelegramForbiddenError as e:
           # Бот заблокирован пользователем
           await self._handle_user_blocked(event, e)
           return None

       except TelegramBadRequest as e:
           # Другие ошибки Telegram API
           if "chat not found" in str(e).lower() or "user not found" in str(e).lower():
               await self._handle_user_not_found(event, e)
           else:
               logger.warning(f"TelegramBadRequest в middleware: {e}")
           return None

   async def _handle_user_blocked(self, event: TelegramObject, error: Exception):
       """Обработка блокировки бота пользователем"""
       user_id = self._extract_user_id(event)
       if not user_id:
           return

       try:
           # Получаем пользователя из БД
           user = await db.get_user(user_id)
           if user:
               # Помечаем пользователя как заблокировавшего бота
               updated_user = User(
                   user_id=user.user_id,
                   username=user.username,
                   status_bot="BLOCKED",  # Помечаем как заблокированный
                   created_at=user.created_at,
                   balance=user.balance,
                   link=user.link,
                   trial=user.trial,
                   trial_end=user.trial_end,
                   referral_count=user.referral_count,
                   first_visit_completed=user.first_visit_completed,
                   subscription_end=user.subscription_end
               )

               await db.update_user(updated_user)

               # Логируем действие
               await db.log_user_action(user_id, "BLOCKED_BOT", "Пользователь заблокировал бота")

               logger.info(f"Пользователь {user_id} заблокировал бота. Статус обновлен в БД.")

       except Exception as e:
           logger.error(f"Ошибка обновления статуса блокировки для пользователя {user_id}: {e}")

   async def _handle_user_not_found(self, event: TelegramObject, error: Exception):
       """Обработка случаев когда пользователь не найден"""
       user_id = self._extract_user_id(event)
       if not user_id:
           return

       logger.info(f"Пользователь {user_id} не найден в Telegram: {error}")

       try:
           # Можно также обновить статус в БД
           user = await db.get_user(user_id)
           if user:
               await db.log_user_action(user_id, "USER_NOT_FOUND", "Пользователь не найден в Telegram")
       except Exception as e:
           logger.error(f"Ошибка логирования 'user not found' для {user_id}: {e}")

   def _extract_user_id(self, event: TelegramObject) -> int:
       """Извлекает user_id из события"""
       try:
           if hasattr(event, 'from_user') and event.from_user:
               return event.from_user.id
           elif hasattr(event, 'chat') and event.chat:
               return event.chat.id
           elif hasattr(event, 'message') and event.message and event.message.from_user:
               return event.message.from_user.id
       except Exception as e:
           logger.error(f"Ошибка извлечения user_id из события: {e}")

       return None


class UserUnblockedMiddleware(BaseMiddleware):
   """
   Middleware для обработки случаев разблокировки бота
   Срабатывает когда пользователь снова начинает взаимодействовать с ботом
   """

   async def __call__(
       self,
       handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
       event: TelegramObject,
       data: Dict[str, Any]
   ) -> Any:
       # Проверяем статус пользователя перед выполнением хэндлера
       user_id = self._extract_user_id(event)
       if user_id:
           await self._check_and_update_unblocked_status(user_id)

       # Выполняем основной хэндлер
       return await handler(event, data)

   async def _check_and_update_unblocked_status(self, user_id: int):
       """Проверяет и обновляет статус разблокированного пользователя"""
       try:
           user = await db.get_user(user_id)
           if user and user.status_bot == "BLOCKED":
               # Пользователь был заблокирован, но снова активен
               updated_user = User(
                   user_id=user.user_id,
                   username=user.username,
                   status_bot="active",  # Возвращаем активный статус
                   created_at=user.created_at,
                   balance=user.balance,
                   link=user.link,
                   trial=user.trial,
                   trial_end=user.trial_end,
                   referral_count=user.referral_count,
                   first_visit_completed=user.first_visit_completed,
                   subscription_end=user.subscription_end
               )

               await db.update_user(updated_user)

               # Логируем разблокировку
               await db.log_user_action(user_id, "UNBLOCKED_BOT", "Пользователь разблокировал бота")

               logger.info(f"Пользователь {user_id} разблокировал бота. Статус обновлен в БД.")

       except Exception as e:
           logger.error(f"Ошибка обновления статуса разблокировки для пользователя {user_id}: {e}")

   def _extract_user_id(self, event: TelegramObject) -> int:
       """Извлекает user_id из события"""
       try:
           if hasattr(event, 'from_user') and event.from_user:
               return event.from_user.id
           elif hasattr(event, 'message') and event.message and event.message.from_user:
               return event.message.from_user.id
       except Exception as e:
           logger.error(f"Ошибка извлечения user_id из события: {e}")

       return None


# Функции для работы с заблокированными пользователями

async def get_blocked_users_count() -> int:
   """Получение количества заблокированных пользователей"""
   try:
       # Этот метод нужно добавить в DatabaseManager
       query = "SELECT COUNT(*) FROM users WHERE status_bot = 'BLOCKED'"
       async with db.pool.acquire() as conn:
           count = await conn.fetchval(query)
           return count or 0
   except Exception as e:
       logger.error(f"Ошибка получения количества заблокированных пользователей: {e}")
       return 0

async def get_blocked_users_list(limit: int = 100) -> list:
   """Получение списка заблокированных пользователей"""
   try:
       query = """
       SELECT user_id, username, created_at
       FROM users
       WHERE status_bot = 'BLOCKED'
       ORDER BY created_at DESC
       LIMIT $1
       """
       async with db.pool.acquire() as conn:
           rows = await conn.fetch(query, limit)
           return [dict(row) for row in rows]
   except Exception as e:
       logger.error(f"Ошибка получения списка заблокированных пользователей: {e}")
       return []

async def cleanup_old_blocked_users(days_threshold: int = 90):
   """
   Очистка старых заблокированных пользователей
   Удаляет пользователей которые заблокировали бота более N дней назад
   """
   try:
       import time
       cutoff_timestamp = int(time.time()) - (days_threshold * 24 * 60 * 60)

       # Сначала логируем что будем удалять
       count_query = """
       SELECT COUNT(*) FROM users
       WHERE status_bot = 'BLOCKED'
       AND created_at < $1
       """

       delete_query = """
       DELETE FROM users
       WHERE status_bot = 'BLOCKED'
       AND created_at < $1
       """

       async with db.pool.acquire() as conn:
           count = await conn.fetchval(count_query, cutoff_timestamp)
           if count > 0:
               await conn.execute(delete_query, cutoff_timestamp)
               logger.info(f"Удалено {count} старых заблокированных пользователей (старше {days_threshold} дней)")
           return count

   except Exception as e:
       logger.error(f"Ошибка очистки старых заблокированных пользователей: {e}")
       return 0



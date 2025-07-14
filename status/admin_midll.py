from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable, Union
import logging

logger = logging.getLogger(__name__)

class AdminMiddleware(BaseMiddleware):
    """Middleware для проверки прав администратора"""

    def __init__(self, admin_ids: list):
        """
        Инициализация middleware

        Args:
            admin_ids (list): Список ID администраторов
        """
        self.admin_ids = set(admin_ids)  # Используем set для быстрого поиска
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any]
    ) -> Any:
        """
        Основная логика middleware

        Args:
            handler: Обработчик события
            event: Событие (Message или CallbackQuery)
            data: Данные контекста
        """
        # Получаем user_id в зависимости от типа события
        if isinstance(event, Message):
            user_id = event.from_user.id
            username = event.from_user.username or "Unknown"
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            username = event.from_user.username or "Unknown"
        else:
            # Для других типов событий пропускаем проверку
            return await handler(event, data)

        # Проверяем, является ли пользователь админом
        if user_id not in self.admin_ids:
            logger.warning(f"Попытка доступа к админ-команде от не-админа: {user_id} (@{username})")

            # Отправляем сообщение о недостатке прав
            if isinstance(event, Message):
                await event.answer("❌ У вас нет прав для выполнения этой команды.")
            elif isinstance(event, CallbackQuery):
                await event.answer("❌ У вас нет прав для выполнения этого действия.", show_alert=True)

            return  # Прерываем выполнение

        # Логируем успешный доступ админа
        logger.info(f"Админ {user_id} (@{username}) выполняет команду")

        # Добавляем информацию о том, что пользователь - админ
        data["is_admin"] = True
        data["admin_id"] = user_id

        # Передаем управление следующему обработчику
        return await handler(event, data)
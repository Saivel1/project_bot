from database import DatabaseManager, User
from aiogram.fsm.context import FSMContext
from typing import Optional
import time
import logging

class DatabaseIntegration:
    """Класс для интеграции базы данных с Telegram ботом"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def init_user_from_message(self, message, state: FSMContext) -> User:
        """
        Инициализация пользователя из сообщения Telegram
        Получает или создает пользователя и синхронизирует с FSM
        """
        user_id = message.from_user.id
        chat_id = message.chat.id
        username = message.from_user.username or ""

        # Получаем или создаем пользователя в БД
        db_user = await self.db.get_or_create_user(user_id, chat_id, username)

        # Синхронизируем данные пользователя с FSM
        await self.sync_user_to_fsm(db_user, state)

        # Логируем действие
        if message.text:
            await self.db.log_user_action(user_id, message="message: " + message.text[:100])

        return db_user

    async def init_user_from_callback(self, callback, state: FSMContext) -> User:
        """
        Инициализация пользователя из callback query
        """
        user_id = callback.from_user.id
        chat_id = callback.message.chat.id
        username = callback.from_user.username or ""

        # Получаем или создаем пользователя в БД
        db_user = await self.db.get_or_create_user(user_id, chat_id, username)

        # Синхронизируем данные пользователя с FSM
        await self.sync_user_to_fsm(db_user, state)

        # Логируем действие
        await self.db.log_user_action(user_id, callback=callback.data)

        return db_user

    async def sync_user_to_fsm(self, user: User, state: FSMContext):
        """Синхронизация данных пользователя из БД в FSM"""
        await update_user_field(state,
            nickname=user.username,
            email=user.email,
            balance=user.balance,
            subscription_end=user.subscription_end,
            link=user.sub_link,
            trial=user.trial,
            trial_end=user.trial_end,
            referral_count=user.refferal_count,
            first_visit_completed=user.first_visit_completed
        )

    async def sync_fsm_to_user(self, callback: CallbackQuery = None, message: Message = None, state: FSMContext = None) -> Optional[User]:
        """Синхронизация данных из FSM в структуру пользователя"""

        # Получаем данные из FSM
        fsm_data = await state.get_data()

        # Определяем user_id
        if callback:
            user_id = callback.from_user.id
        elif message:
            user_id = message.from_user.id
        else:
            return None

        # Получаем текущего пользователя из БД
        current_user = await self.db.get_user(user_id)
        if not current_user:
            return None

        # Обновляем данные из FSM
        updated_user = User(
            user_id=current_user.user_id,
            chat_id=current_user.chat_id,
            username=fsm_data.get('nickname', current_user.username),
            status_bot=fsm_data.get('status_bot', current_user.status_bot),
            created_at=current_user.created_at,
            email=fsm_data.get('email', current_user.email),
            balance=fsm_data.get('balance', current_user.balance),
            sub_link=fsm_data.get('sub_link', current_user.sub_link),
            trial=fsm_data.get('trial', current_user.trial),
            trial_end=fsm_data.get('trial_end', current_user.trial_end),
            refferal_count=fsm_data.get('refferal_count', current_user.refferal_count),
            first_visit_completed=fsm_data.get('first_visit_completed', current_user.first_visit_completed)
        )

        # Сохраняем обновленного пользователя
        return updated_user

    async def save_user_changes(self, state: FSMContext, callback: CallbackQuery = None, message: Message = None) -> bool:
        """Сохранение изменений пользователя из FSM в БД"""
        user = await self.sync_fsm_to_user(callback=callback, message=message, state=state)
        if not user:
            return False

        return await self.db.update_user(user)

    async def update_user_balance(self, user_id: int, new_balance: int, state: FSMContext) -> bool:
        """Обновление баланса пользователя"""
        user = await self.db.get_user(user_id)
        if not user:
            return False

        updated_user = User(
            user_id=user.user_id,
            chat_id=user.chat_id,
            username=user.username,
            status_bot=user.status_bot,
            created_at=user.created_at,
            email=user.email,
            balance=new_balance,
            sub_link=user.sub_link,
            trial=user.trial,
            trial_end=user.trial_end,
            refferal_count=user.refferal_count,
            first_visit_completed=user.first_visit_completed
        )

        success = await self.db.update_user(updated_user)
        if success:
            # Обновляем FSM
            await state.update_user_field(balance=new_balance)

        return success

    async def update_user_email(self, user_id: int, email: str, state: FSMContext) -> bool:
        """Обновление email пользователя"""
        user = await self.db.get_user(user_id)
        if not user:
            return False

        updated_user = User(
            user_id=user.user_id,
            chat_id=user.chat_id,
            username=user.username,
            status_bot=user.status_bot,
            created_at=user.created_at,
            email=email,
            balance=user.balance,
            sub_link=user.sub_link,
            trial=user.trial,
            trial_end=user.trial_end,
            refferal_count=user.refferal_count,
            first_visit_completed=user.first_visit_completed
        )

        success = await self.db.update_user(updated_user)
        if success:
            # Обновляем FSM
            await state.update_data(email=email)

        return success

    async def activate_trial(self, user_id: int, trial_days: int = 7) -> bool:
        """Активация пробного периода"""
        user = await self.db.get_user(user_id)
        if not user or user.trial != "never_used":
            return False

        trial_end_timestamp = int(time.time()) + (trial_days * 24 * 60 * 60)

        updated_user = User(
            user_id=user.user_id,
            chat_id=user.chat_id,
            username=user.username,
            status_bot=user.status_bot,
            created_at=user.created_at,
            email=user.email,
            balance=user.balance,
            sub_link=user.sub_link,
            trial="active",
            trial_end=trial_end_timestamp,
            refferal_count=user.refferal_count,
            first_visit_completed=user.first_visit_completed
        )

        return await self.db.update_user(updated_user)

    async def is_subscription_active(self, user_id: int) -> bool:
        """Проверка активности подписки пользователя"""
        user = await self.db.get_user(user_id)
        if not user:
            return False

        current_time = int(time.time())

        # Проверяем пробный период
        if user.trial == "active" and user.trial_end > current_time:
            return True

        # Проверяем платную подписку (если balance > 0, значит была оплата)
        if user.balance > 0:
            return True

        return False

    async def process_payment_success(self, user_id: int, amount: int, payment_id: int) -> bool:
        """Обработка успешного платежа"""
        # Обновляем статус платежа
        await self.db.update_payment_status(payment_id, "completed")

        # Обновляем баланс пользователя
        user = await self.db.get_user(user_id)
        if not user:
            return False

        new_balance = user.balance + amount

        updated_user = User(
            user_id=user.user_id,
            chat_id=user.chat_id,
            username=user.username,
            status_bot=user.status_bot,
            created_at=user.created_at,
            email=user.email,
            balance=new_balance,
            sub_link=user.sub_link,
            trial=user.trial,
            trial_end=user.trial_end,
            refferal_count=user.refferal
from keyboards import personal_acc as per_acc
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dataclasses import dataclass, asdict
from typing import Optional
import re
from status.status_keys import get_message_by_status

class EmailForm(StatesGroup):
    waiting_for_email = State()


@dataclass(slots=True, frozen=True)
class UserData:
    """Структура данных пользователя для FSMContext"""
    email: Optional[str] = None
    balance: int = 0
    trial: str = 'never_used'
    subscription_end: Optional[str] = None
    nickname: Optional[str] = None
    referral_count: int = 0
    last_activity: Optional[float] = None

async def get_user_data(state: FSMContext) -> UserData:
    """Получает данные пользователя из FSM как dataclass"""
    data = await state.get_data()
    return UserData(
        email=data.get('email'),
        balance=data.get('balance', 0),
        trial=data.get('trial', 'never_used'),
        subscription_end=data.get('subscription_end'),
        nickname=data.get('nickname'),
        referral_count=data.get('referral_count', 0),
        last_activity=data.get('last_activity')
    )

async def save_user_data(state: FSMContext, user_data: UserData):
    """Сохраняет dataclass в FSM"""
    # Конвертируем dataclass в словарь и сохраняем
    await state.update_data(**asdict(user_data))

async def update_user_field(state: FSMContext, **kwargs) -> UserData:
    """Обновляет конкретные поля пользователя"""
    current = await get_user_data(state)
    current_dict = asdict(current)
    current_dict.update(kwargs)
    updated = UserData(**current_dict)
    await save_user_data(state, updated)
    return updated


SIMPLE_EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

router = Router()

used = 0

def is_valid_email_simple(email: str) -> bool:
    if not email or not isinstance(email, str):
        return False
    return bool(re.match(SIMPLE_EMAIL_PATTERN, email.strip()))

def create_personal_acc_text(balance: int = 0, used: int = 0, email: str = None) -> str:
    email_text = email if email else "Не указан"
    balance_text = balance if balance else 0
    return f"""
📊 Личный кабинет

💰 Ваш баланс: {balance_text} ₽
📈 Использовано: {used} ГБ
📧 Ваш email: {email_text}
    """.strip()


@router.callback_query(F.data == 'trial_per')
async def trial_per(callback: CallbackQuery, state: FSMContext):
    user_data = await get_user_data(state)
    # Активируем пробный период
    user_data = await update_user_field(state, trial='in_progress')
    # Используем функцию для получения правильного сообщения
    message = get_message_by_status('start_menu', user_data.trial, user_data.balance)
    await callback.message.edit_text(
        text=message['text'],
        reply_markup=message['keyboard']
    )

@router.callback_query(F.data == 'personal_acc')
async def personal_acc(callback: CallbackQuery, state: FSMContext):
    user_data = await get_user_data(state)
    text_message = create_personal_acc_text(user_data.balance, used, user_data.email)

    if user_data.trial == 'never_used':
        keyboard = per_acc.VPNPersAccKeyboards.personal_acc_new()
    else:
        keyboard = per_acc.VPNPersAccKeyboards.personal_acc()
    await callback.message.edit_text(
        text=text_message,
        reply_markup=keyboard
    )

@router.callback_query(F.data.in_(["to_pay_year", "to_pay_6_months", "to_pay_3_months", "to_pay_month"]))
async def handler_payment_success(callback: CallbackQuery, state: FSMContext):
    user_data = await get_user_data(state)
    plan = {
        "to_pay_year": 600,
        "to_pay_6_months": 300,
        "to_pay_3_months": 150,
        "to_pay_month": 50
    }
    new_balance = user_data.balance + plan[callback.data]
    await update_user_field(state, balance=new_balance)

    message = get_message_by_status("payment_success", user_data.trial, user_data.balance)

    await callback.message.edit_text(
        text=message['text'],
        reply_markup=message['keyboard']
    )

@router.callback_query(F.data == "change_email")
async def request_email_with_state(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EmailForm.waiting_for_email)
    await callback.message.answer("📧 Введите ваш email:")
    await callback.answer()

@router.message(EmailForm.waiting_for_email, F.text)
async def process_email(message: Message, state: FSMContext):
    email = message.text.strip()

    if is_valid_email_simple(email):
        await state.update_data(email=email)
        await state.set_state(None)
        keyboard = per_acc.VPNPersAccKeyboards.change_email()
        await message.answer(f"✅ Email {email} сохранен!", reply_markup=keyboard)

    else:
        await message.answer("❌ Неправильный формат email. Попробуйте еще раз:")

@router.callback_query(F.data.in_(['buy_key', 'buy_key_in_install']))
async def buy_key(callback: CallbackQuery, state: FSMContext):
    user_data = await get_user_data(state)
    if user_data.email is None:
        await state.set_state(EmailForm.waiting_for_email)
        await callback.message.answer("📧 Введите ваш email:")
        await callback.answer()
    else:
        message = get_message_by_status(callback.data, user_data.trial, user_data.balance)
        await callback.message.edit_text(
            text=message['text'],
            reply_markup=message['keyboard']
        )




# ==========================================
# Универсальный хэндлер с условиями
# ==========================================

@router.callback_query()
async def universal_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await get_user_data(state)

    # Используем функцию для получения сообщения по статусу
    message = get_message_by_status(callback.data, user_data.trial, user_data.balance)

    await callback.message.edit_text(
        text=message['text'],
        reply_markup=message['keyboard']
    )

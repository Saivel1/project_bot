from os import link
from keyboards import personal_acc as per_acc
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dataclasses import dataclass, asdict
from typing import Optional
import re
from status.status_keys import get_message_by_status
from datetime import datetime
from marzban.Backend import MarzbanBackendContext

class EmailForm(StatesGroup):
    waiting_for_email = State()

@dataclass(slots=True, frozen=True)
class UserData:
    """Структура данных пользователя для FSMContext"""
    email: Optional[str] = None
    balance: int = 0
    trial: str = 'never_used'
    subscription_end: int = 0
    nickname: Optional[str] = None
    referral_count: int = 0
    link: Optional[str] = None

async def get_user_data(state: FSMContext) -> UserData:
    """Получает данные пользователя из FSM как dataclass"""
    data = await state.get_data()
    return UserData(
        email=data.get('email'),
        balance=data.get('balance', 0),
        trial=data.get('trial', 'never_used'),
        subscription_end=data.get('subscription_end', 0),
        nickname=data.get('nickname'),
        referral_count=data.get('referral_count', 0),
        link=data.get('link')
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

def create_personal_acc_text(balance: int = 0, used: int = 0, email: str = '', subscription_end: int = 0) -> str:
    current_date = int(datetime.timestamp(datetime.now()))
    email_text = email if email else "Не указан"
    balance_text = balance if balance else 0
    if current_date > subscription_end:
        sub_text = 0
        hours = 0
    else:
        sub_text = (subscription_end - current_date)//86400 if subscription_end else 0
        hours = ((subscription_end - current_date)//3600 - sub_text * 24) if subscription_end else 0
    return f"""
📊 Личный кабинет

💰 Потрачено в сервисе: {balance_text} ₽
💰 Дней подписки: {int(sub_text)} | Часов: {int(hours)}
📈 Использовано: {used} ГБ
📧 Ваш email: {email_text}
    """.strip()

@router.message(EmailForm.waiting_for_email, F.text == "/cancel")
async def cancel_email(message: Message, state: FSMContext):
    user_data = await get_user_data(state)
    await state.set_state(None)
    await message.answer("Отмена операции.")
    messages = get_message_by_status('start_menu', user_data.trial, user_data.subscription_end)
    await message.answer(
        text=messages['text'],
        reply_markup=messages['keyboard']
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

@router.callback_query(EmailForm.waiting_for_email)
async def after_change_email(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("📧 Введите ваш email: \n Или /cancel для отмены операции.")
    await callback.answer()

@router.callback_query(F.data == 'trial_per')
async def trial_per(callback: CallbackQuery, state: FSMContext):
    user_data = await get_user_data(state)
    current_date = datetime.timestamp(datetime.now())

    # Активируем пробный период
    user_data = await update_user_field(state, trial='in_progress')
    # Используем функцию для получения правильного сообщения
    message = get_message_by_status('start_menu', user_data.trial, user_data.subscription_end)
    # Будет увеличиваться на N дней, пока остаётся нетронутым.
    n_days = 30
    if current_date > user_data.subscription_end:
        new_date = current_date + (n_days * 86400)
        await update_user_field(state, subscription_end=new_date)
    else:
        new_date = user_data.subscription_end + (n_days * 86400)
        await update_user_field(state, subscription_end=new_date)


    await callback.message.edit_text(
        text=message['text'],
        reply_markup=message['keyboard']
    )

@router.callback_query(F.data == 'personal_acc')
async def personal_acc(callback: CallbackQuery, state: FSMContext):
    
    async with MarzbanBackendContext() as backend:
        res = await backend.get_user(str(callback.from_user.id))
        if not res:
            new_link = None
            await update_user_field(state, link=new_link)
            
    user_data = await get_user_data(state)

    text_message = create_personal_acc_text(user_data.balance, used, user_data.email, user_data.subscription_end)
    link = user_data.link if user_data.link and (user_data.trial != 'never_used' or user_data.subscription_end) else "Пока пусто."
    if user_data.trial == 'never_used':
        keyboard = per_acc.VPNPersAccKeyboards.personal_acc_new()
    else:
        keyboard = per_acc.VPNPersAccKeyboards.personal_acc()
    await callback.message.edit_text(
        text=f'{text_message} \n\n Ссылка на подписку: {link}',
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

    current_date = int(datetime.timestamp(datetime.now()))
    new_balance = user_data.balance + plan[callback.data]

    print(f'Это дата: {current_date}')
    
    if current_date > user_data.subscription_end:
        new_date = current_date + (plan[callback.data] * 86400)//50
        await update_user_field(state, subscription_end=new_date)
    else:
        new_date = user_data.subscription_end + (plan[callback.data] * 86400)//50
        await update_user_field(state, subscription_end=new_date)
    print(f'Это дата: {current_date} | А это новый баланс: {new_date}')
    await update_user_field(state, balance=new_balance)

    message = get_message_by_status("payment_success", user_data.trial, user_data.subscription_end)

    await callback.message.edit_text(
        text=message['text'],
        reply_markup=message['keyboard']
    )


@router.callback_query(F.data.in_(['buy_key', 'buy_key_in_install']))
async def buy_key(callback: CallbackQuery, state: FSMContext):
    user_data = await get_user_data(state)
    if user_data.email is None:
        await state.set_state(EmailForm.waiting_for_email)
        await callback.message.answer("📧 Введите ваш email:")
        await callback.answer()
    else:
        message = get_message_by_status(callback.data, user_data.trial, user_data.subscription_end)
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
    message = get_message_by_status(callback.data, user_data.trial, user_data.subscription_end)
    await callback.message.edit_text(
        text=message['text'],
        reply_markup=message['keyboard']
    )

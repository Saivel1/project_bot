from keyboards import vpn_keyboards as vpn, start_menu, help_keyboards as help_k, personal_acc as per_acc, refferal
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
import re
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass(slots=True, frozen=True)
class UserData:
    """Структура данных пользователя для FSMContext"""
    email: Optional[str] = None
    balance: int = 0
    status: str = 'inactive'
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
        status=data.get('status', 'inactive'),
        subscription_end=data.get('subscription_end'),
        nickname=data.get('nickname'),
        referral_count=data.get('referral_count', 0),
        last_activity=data.get('last_activity')
    )

async def save_user_data(state: FSMContext, user_data: UserData):
    """Сохраняет dataclass в FSM"""
    # Конвертируем dataclass в словарь и сохраняем
    await state.update_data(**asdict(user_data))



class EmailForm(StatesGroup):
    waiting_for_email = State()

class NicknameForm(StatesGroup):
    waiting_for_nickname = State()

SIMPLE_EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
NICKNAME_PATTERN = r'@[a-zA-Z0-9._%+-]+'

router = Router()

# Объединенный словарь всех сообщений
ALL_MESSAGES = {
    # Основные меню
    'start_menu': {
        'text': '🏠 Главное меню\nВыберите нужное действие:',
        'keyboard': start_menu.start_menu_keyboard()
    },
    'not_paid': {
        'text': '🔒 VPN не активирован\n\nДля использования VPN необходимо приобрести ключ.',
        'keyboard': vpn.VPNInstallKeyboards.not_paid_install()
    },
    'install_vpn': {
        'text': '✅ VPN активирован\nВыберите платформу для установки:',
        'keyboard': vpn.VPNInstallKeyboards.choose_platform('start_menu')
    },
    'android': {
        'text': '🤖 Android\n\nИнструкция по установке для Android...',
        'keyboard': vpn.VPNInstallKeyboards.android_platform()
    },
    'ios': {
        'text': '🍎 iOS/MacOS\n\nИнструкция по установке для iOS/MacOS...',
        'keyboard': vpn.VPNInstallKeyboards.ios_platform()
    },
    'windows': {
        'text': '🪟 Windows\n\nИнструкция по установке для Windows...',
        'keyboard': vpn.VPNInstallKeyboards.windows_platform()
    },
    'extend_sub': {
        'text': 'Продлить подписку',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('start_menu')
    },

    # Помощь
    'help': {
        'text': 'Помощь главная страница, здесь будет всё, что касается помощи',
        'keyboard': help_k.HelpKeyboards.help_main()
    },
    'help_install_vpn': {
        'text': 'Это кнопки функции "help_install_vpn" \n\n Если есть проблемы с установка VPN',
        'keyboard': help_k.HelpKeyboards.help_install_vpn()
    },
    'help_per_acc': {
        'text': 'Это кнопки функции "help_per_acc" \n\n Если есть проблемы с оплатой или ЛК',
        'keyboard': help_k.HelpKeyboards.help_per_acc()
    },
    'help_period': {
        'text': 'Это кнопки функции "help_per_acc" \n\n Если есть проблемы с пробным периодом',
        'keyboard': help_k.HelpKeyboards.help_period()
    },
    'help_refferal': {
        'text': 'Это кнопки функции "help_per_acc" \n\n Если есть проблемы с реферальной программой',
        'keyboard': help_k.HelpKeyboards.help_refferal()
    },

    # Личный кабинет
    'change_email': {
        'text': 'Напиши свой email для отправки чеков в формате никнейм@почта.',
        'keyboard': per_acc.VPNPersAccKeyboards.change_email()
    },
    'buy_key': {
        'text': 'Выбери подписку',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('personal_acc')
    },
    'decline_ch_acc': {
        'text' : 'Операция отменена',
        'keyboard' : per_acc.VPNPersAccKeyboards.change_email()
    },

    # Реферальная программа
    'refferal': {
        'text': 'Реферальная программа',
        'keyboard': refferal.VPNRefferalKeyboards.refferal_menu()
    },
    'invite': {
        'text': 'Пригласить друга',
        'keyboard': refferal.VPNRefferalKeyboards.invite_menu()
    }
}


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

# =============================================================================
# УНИВЕРСАЛЬНЫЙ ХЭНДЛЕР ДЛЯ ВСЕХ ПРОСТЫХ СООБЩЕНИЙ
# =============================================================================

@router.callback_query(F.data.in_(list(ALL_MESSAGES.keys())) & ~F.data.in_(["change_email"]))
async def universal_message_handler(callback: CallbackQuery):
    message_data = ALL_MESSAGES[callback.data]
    await callback.message.edit_text(
        text=message_data['text'],
        reply_markup=message_data['keyboard']
    )

# =============================================================================
# СПЕЦИАЛЬНЫЕ ХЭНДЛЕРЫ
# =============================================================================

# Личный кабинет с данными из state
@router.callback_query(F.data == "personal_acc")
async def handler_personal_acc(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    email = data.get('email')
    balance = data.get('balance')

    text = create_personal_acc_text(balance, used, email)
    keyboard = per_acc.VPNPersAccKeyboards.personal_acc()

    await callback.message.edit_text(text, reply_markup=keyboard)

# Email запрос
@router.callback_query(F.data == "change_email")
async def request_email_with_state(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EmailForm.waiting_for_email)
    await callback.message.answer("📧 Введите ваш email:")
    await callback.answer()

# Email обработка
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

# Обработка платежей
@router.callback_query(F.data.in_(["to_pay_year", "to_pay_6_months", "to_pay_3_months", "to_pay_month"]))
async def handler_payment_success(callback: CallbackQuery):
    """После успешной оплаты показываем меню установки VPN"""
    await callback.message.edit_text(
        text='✅ VPN активирован\nВыберите платформу для установки:',
        reply_markup=vpn.VPNInstallKeyboards.choose_platform('personal_acc')
    )

# Nickname запрос
@router.callback_query(F.data == "swap_acc")
async def request_email_with_state(callback: CallbackQuery, state: FSMContext):
    await state.set_state(NicknameForm.waiting_for_nickname)
    await state.update_data(balance=15)
    await callback.message.answer("Введите новый никнейм:")
    await callback.answer()

# Nickname обработка
@router.message(NicknameForm.waiting_for_nickname, F.text)
async def process_nickname(message: Message, state: FSMContext):
    nickname = message.text.strip()

    if re.match(NICKNAME_PATTERN, nickname):
        await state.set_state(None)
        await state.update_data(nickname=nickname)

        keyboard = per_acc.VPNPersAccKeyboards.changing_nickname()
        await message.answer(f"✅ Новый никнейм {nickname}. Вы точно хотите его изменить? \n После нажатия на кнопку {"продолжить"} на вашем счету будет 0 руб.", reply_markup=keyboard)
    else:
        await message.answer("❌ Неправильный формат никнейма. Попробуйте еще раз:")

# Отмена смены никнейма
@router.callback_query(F.data == "decline_ch_acc")
async def decline_ch_acc_pressed(callback: CallbackQuery, state: FSMContext):
    await state.update_data(nickname=None)
    await state.set_state(None)
    message = ALL_MESSAGES[callback.data]
    await callback.message.edit_text(
        text=message['text'],
        reply_markup=message['keyboard']
    )

# Подтверждение смены никнейма
@router.callback_query(F.data == "accept_ch_acc")
async def accept_ch_acc_pressed(callback: CallbackQuery, state: FSMContext):
    await state.update_data(balance=0)

    # Сразу показываем личный кабинет с обновленным балансом
    data = await state.get_data()
    email = data.get('email')
    balance = data.get('balance')  # Будет 0

    text = create_personal_acc_text(balance, used, email)
    keyboard = per_acc.VPNPersAccKeyboards.personal_acc()

    await callback.message.edit_text(
        f"✅ Операция совершена!\n\n{text}",
        reply_markup=keyboard
    )
from keyboards import vpn_keyboards as vpn, start_menu, help_keyboards as help_k, personal_acc as per_acc, refferal
from config_data.config import load_config_help

config = load_config_help('.env')
help_acc = config.tg.tg_user
platform = ''

# =============================================================================
# ОБЩИЕ КНОПКИ (НЕ ЗАВИСЯТ ОТ СТАТУСА)
# =============================================================================

COMMON_BUTTONS = {
    'invite':{
        'text': "Пригласить друга",
        'keyboard': refferal.VPNRefferalKeyboards.invite_menu('refferal')
    },
    'help': {
        'text': 'Помощь',
        'keyboard': help_k.HelpKeyboards.help_main_new('start_menu')
    },
    'help_install_vpn': {
        'text': 'Помощь с установкой VPN',
        'keyboard': help_k.HelpKeyboards.help_main_new('install_vpn')
    },
    'help_per_acc_in_per_acc': {
        'text': 'Помощь с оплатой и личным кабинетом',
        'keyboard': help_k.HelpKeyboards.help_per_acc('personal_acc')
    },
    'help_per_acc': {
        'text': 'Помощь с оплатой и личным кабинетом',
        'keyboard': help_k.HelpKeyboards.help_per_acc('help')
    },
    'help_period': {
        'text': 'Помощь с пробным периодом',
        'keyboard': help_k.HelpKeyboards.help_period()
    },
    'help_refferal': {
        'text': 'Помощь с реферальной программой',
        'keyboard': help_k.HelpKeyboards.help_refferal('help')
    },
    'help_to_me': {
        'text': f'Напиши {help_acc}',
        'keyboard': help_k.HelpKeyboards.help_message()
    },
    'help_refferal_in_refferal': {
        'text': 'Помощь с реферальной программой',
        'keyboard': help_k.HelpKeyboards.help_refferal('refferal')
    }
}

# =============================================================================
# СООБЩЕНИЯ ДЛЯ НОВЫХ ПОЛЬЗОВАТЕЛЕЙ (С ПРОБНЫМ ПЕРИОДОМ)
# =============================================================================

TRAIL_NOT_USED = {
    'start_menu': {
        'text': "Добро пожаловать! Ваш статус Неактивен. Подписки НЕТ.",
        'keyboard': start_menu.start_menu_keyboard_trail()
    },
    'install_vpn': {
        'text': 'У вас нет ключа, или срок его действия закончился.',
        'keyboard': vpn.VPNInstallKeyboards.not_paid_install_new('start_menu')
    },
    'buy_key_in_install': {
        'text': 'Пополнить баланс',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu_new('install_vpn')
    },
    'invite_in_install': {
        'text': 'Пригласить друга',
        'keyboard': refferal.VPNRefferalKeyboards.invite_menu('install_vpn')
    },
    'buy_key': {
        'text': 'Пополнить баланс',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu_new('personal_acc')
    },
    'refferal': {
        'text': 'Пригласить друга',
        'keyboard': refferal.VPNRefferalKeyboards.refferal_menu()
    }
}

# =============================================================================
# СООБЩЕНИЯ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ С АКТИВНЫМ ПРОБНЫМ ПЕРИОДОМ И ОПЛАЧЕНОЙ ПОДПИСКОЙ
# =============================================================================

TRAIL_NOT_USED_PAID = {
    'start_menu': {
        'text': "Добро пожаловать! Подписка активна, но не активирован пробный период.",
        'keyboard': start_menu.start_menu_keyboard_trail_extend()
    },
    'install_vpn': {
        'text': 'Выберите платформу',
        'keyboard': vpn.VPNInstallKeyboards.choose_platform('start_menu')
    },
    'buy_key_in_install': {
        'text': 'Пополнить баланс',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu_new('install_vpn')
    },
    'invite_in_install': {
        'text': 'Пригласить друга',
        'keyboard': refferal.VPNRefferalKeyboards.invite_menu('install_vpn')
    },
    'buy_key': {
        'text': 'Пополнить баланс',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu_new('personal_acc')
    },
    'refferal': {
        'text': 'Пригласить друга',
        'keyboard': refferal.VPNRefferalKeyboards.refferal_menu()
    }
}

# =============================================================================
# СООБЩЕНИЯ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ С АКТИВИРОВАННЫМ ПРОБНЫМ ПЕРИОДОМ
# =============================================================================

TRIAL_IN_PROGRESS_NOT_PAID = {
    'start_menu': {
        'text': "Добро пожаловать! \n Пробный период активен! \n Подписки НЕТ.",
        'keyboard': start_menu.start_menu_keyboard_trial_in_progress()
    },
    'install_vpn': {
        'text': 'Выберите платформу',
        'keyboard': vpn.VPNInstallKeyboards.choose_platform('start_menu')
    },
    'buy_key_in_install': {
        'text': 'Пополнить баланс',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('install_vpn')
    },
    'invite_in_install': {
        'text': 'Пригласить друга',
        'keyboard': refferal.VPNRefferalKeyboards.invite_menu('install_vpn')
    },
    'buy_key': {
        'text': 'Пополнить баланс',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('start_menu')
    },
    'refferal': {
        'text': 'Пригласить друга',
        'keyboard': refferal.VPNRefferalKeyboards.refferal_menu()
    }
}

# =============================================================================
# ОБЩИЕ СООБЩЕНИЯ (НЕЗАВИСИМО ОТ СТАТУСА)
# =============================================================================

PAID = {
    'payment_success': {
        'text': 'Оплата прошла успешно!',
        'keyboard': help_k.HelpKeyboards.help_message()
    },
    'start_menu': {
        'text': 'Добро пожаловать!',
        'keyboard': start_menu.start_menu_keyboard()
    },
    'extend_sub': {
        'text': 'Продлить подписку',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('start_menu')
    },
    'install_vpn': {
        'text': 'Выберите платформу',
        'keyboard': vpn.VPNInstallKeyboards.choose_platform('start_menu')
    },
    'invite_in_install': {
        'text': 'Пригласить друга',
        'keyboard': refferal.VPNRefferalKeyboards.invite_menu('install_vpn')
    },
    'buy_key': {
        'text': 'Пополнить баланс',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('personal_acc')
    },
    'refferal': {
        'text': 'Пригласить друга',
        'keyboard': refferal.VPNRefferalKeyboards.refferal_menu()
    }
}

# =============================================================================
# ПОМОЩЬ В ЛИЧНЫЕ СООБЩЕНИЯ
# =============================================================================

TO_ME = ['help_refferal_not_add', 'help_period_not_active', 'help_bank', 'help_paid_not_active', 'help_link_inactive']
PLATFORM = ['android', 'ios', 'windows']

def swap_platform(a: str) -> dict:
    values = {
        'platform_text': {
            'text': f'Платформа {a}',
            'keyboard': vpn.VPNInstallKeyboards.platform_chosen()
        }
    }
    return values['platform_text']

# =============================================================================
# ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ СООБЩЕНИЙ
# =============================================================================

def get_message_by_status(callback_data: str, trial: str, balance: int = 0) -> dict:
    """
    Возвращает сообщение в зависимости от статуса пользователя

    Args:
        callback_data: Название действия (start_menu, install_vpn, etc.)
        status: Статус пользователя (new, active, expired)
        trial: Активирован ли пробный период

    Returns:
        Словарь с текстом и клавиатурой
    """

    # Сначала ищем в общих кнопках
    if callback_data in COMMON_BUTTONS:
        return COMMON_BUTTONS[callback_data]

    if callback_data == 'payment_success':
        message = PAID['payment_success']
        return message

    # Выбираем словарь сообщений по статусу
    if trial == 'never_used' and balance == 0:
        messages = TRAIL_NOT_USED
    elif trial == 'never_used' and balance > 0:
        messages = TRAIL_NOT_USED_PAID
    elif trial == 'in_progress' and balance == 0:
        messages = TRIAL_IN_PROGRESS_NOT_PAID
    elif trial == 'expired' and balance == 0:
        messages = MUST_PAY
    else:
        messages = PAID

    if callback_data in TO_ME:
        message = COMMON_BUTTONS.get('help_to_me')
        return message
    elif callback_data in PLATFORM:
        message = swap_platform(callback_data)
        return message

    # Ищем конкретное сообщение
    message = messages.get(callback_data)

    return message

STATUS_VAR = {
    'trial' : {
        'never_used': 'Не использовано',
        'in_progress': 'Используется',
        'expired': 'Истекло'
    },
    'status': {
        'not_paid': 'Не оплачен',
        'paid': 'Оплачен'
    }
}
from keyboards import vpn_keyboards as vpn, start_menu, help_keyboards as help_k, personal_acc as per_acc, refferal
from config_data.config import load_config_help

config = load_config_help('.env')
help_acc = config.tg.tg_user

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
        'text': f'Для решения вашей проблемы напишите {help_acc}',
        'keyboard': help_k.HelpKeyboards.help_message()
    },
    'help_refferal_in_refferal': {
        'text': 'Помощь с реферальной программой',
        'keyboard': help_k.HelpKeyboards.help_refferal('refferal')
    }
}

# =============================================================================
# СООБЩЕНИЯ ДЛЯ НОВЫХ ПОЛЬЗОВАТЕЛЕЙ (БЕЗ ПРОБНОГО ПЕРИОДА)
# =============================================================================

TRAIL_NOT_USED = {
    'start_menu': {
        'text': "🏠 Главное меню\n\n❌ Статус: Неактивен\n🎁 Пробный период: Доступен\n💰 Подписка: Отсутствует",
        'keyboard': start_menu.start_menu_keyboard_trail()
    },
    'install_vpn': {
        'text': '❌ У вас нет активной подписки\n\nДля использования VPN необходимо:\n• Активировать пробный период\n• Или приобрести подписку',
        'keyboard': vpn.VPNInstallKeyboards.not_paid_install_new('start_menu')
    },
    'buy_key_in_install': {
        'text': '💳 Выберите тариф подписки:',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu_new('install_vpn')
    },
    'invite_in_install': {
        'text': '👥 Пригласите друга и получите бонусы!',
        'keyboard': refferal.VPNRefferalKeyboards.invite_menu('install_vpn')
    },
    'buy_key': {
        'text': '💳 Выберите тариф подписки:',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu_new('personal_acc')
    },
    'refferal': {
        'text': '👥 Реферальная программа\n\nПриглашайте друзей и получайте бонусы!',
        'keyboard': refferal.VPNRefferalKeyboards.refferal_menu()
    }
}

# =============================================================================
# СООБЩЕНИЯ ДЛЯ НОВЫХ ПОЛЬЗОВАТЕЛЕЙ С ОПЛАЧЕННОЙ ПОДПИСКОЙ
# =============================================================================

TRAIL_NOT_USED_PAID = {
    'start_menu': {
        'text': "🏠 Главное меню\n\n✅ Статус: Активен\n🎁 Пробный период: Доступен\n💰 Подписка: Активна",
        'keyboard': start_menu.start_menu_keyboard_trail_extend()
    },
    'install_vpn': {
        'text': """Выбери платформу:

🤖 Android -  Защити свой Android!  Инструкция по установке VPN на Android телефоны и планшеты.

🍏 IOS/MacOS -  Инструкция для iPhone, iPad и Mac.  Получи инструкцию по установке VPN на устройства Apple.

💻 Windows -  Инструкция для Windows.  Получи подробную инструкцию по установке VPN на платформе Windows.""",
        'keyboard': vpn.VPNInstallKeyboards.choose_platform('start_menu')
    },
    'buy_key_in_install': {
        'text': '💳 Выберите тариф для продления:',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu_new('install_vpn')
    },
    'invite_in_install': {
        'text': '👥 Пригласите друга и получите бонусы!',
        'keyboard': refferal.VPNRefferalKeyboards.invite_menu('install_vpn')
    },
    'buy_key': {
        'text': '💳 Выберите тариф для продления:',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu_new('personal_acc')
    },
    'extend_sub': {
        'text': '💳 Выберите тариф для продления:',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('start_menu')
    },
    'refferal': {
        'text': '👥 Реферальная программа\n\nПриглашайте друзей и получайте бонусы!',
        'keyboard': refferal.VPNRefferalKeyboards.refferal_menu()
    }
}

# =============================================================================
# СООБЩЕНИЯ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ С АКТИВНЫМ ПРОБНЫМ ПЕРИОДОМ
# =============================================================================

TRIAL_IN_PROGRESS_NOT_PAID = {
    'start_menu': {
        'text': "🏠 Главное меню\n\n✅ Статус: Активен\n🎁 Пробный период: Используется\n💰 Подписка: Отсутствует",
        'keyboard': start_menu.start_menu_keyboard_trial_in_progress()
    },
    'install_vpn': {
        'text': """Выбери платформу:

🤖 Android -  Защити свой Android!  Инструкция по установке VPN на Android телефоны и планшеты.

🍏 IOS/MacOS -  Инструкция для iPhone, iPad и Mac.  Получи инструкцию по установке VPN на устройства Apple.

💻 Windows -  Инструкция для Windows.  Получи подробную инструкцию по установке VPN на платформе Windows.""",
        'keyboard': vpn.VPNInstallKeyboards.choose_platform('start_menu')
    },
    'buy_key_in_install': {
        'text': '💳 Выберите тариф подписки:',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('install_vpn')
    },
    'invite_in_install': {
        'text': '👥 Пригласите друга и получите бонусы!',
        'keyboard': refferal.VPNRefferalKeyboards.invite_menu('install_vpn')
    },
    'buy_key': {
        'text': '💳 Выберите тариф подписки:',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('start_menu')
    },
    'refferal': {
        'text': '👥 Реферальная программа\n\nПриглашайте друзей и получайте бонусы!',
        'keyboard': refferal.VPNRefferalKeyboards.refferal_menu()
    }
}

# =============================================================================
# СООБЩЕНИЯ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ С ИСТЕКШИМ ПРОБНЫМ ПЕРИОДОМ
# =============================================================================

MUST_PAY = {
    'start_menu': {
        'text': "🏠 Главное меню\n\n❌ Статус: Неактивен\n⏰ Пробный период: Истек\n💰 Подписка: Отсутствует\n\nДля продолжения использования VPN необходимо приобрести подписку.",
        'keyboard': start_menu.start_menu_keyboard()
    },
    'install_vpn': {
        'text': '❌ У вас нет активной подписки\n\n⏰ Пробный период истек\nДля использования VPN необходимо приобрести подписку.',
        'keyboard': vpn.VPNInstallKeyboards.not_paid_install('start_menu')
    },
    'buy_key': {
        'text': '💳 Выберите тариф подписки:',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('personal_acc')
    },
    'extend_sub': {
        'text': '💳 Выберите тариф подписки:',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('start_menu')
    },
    'refferal': {
        'text': '👥 Реферальная программа\n\nПриглашайте друзей и получайте бонусы!',
        'keyboard': refferal.VPNRefferalKeyboards.refferal_menu()
    }
}

# =============================================================================
# ОБЩИЕ СООБЩЕНИЯ ДЛЯ ОПЛАЧЕННЫХ ПОЛЬЗОВАТЕЛЕЙ
# =============================================================================

PAID = {
    'payment_success': {
        'text': '✅ Оплата прошла успешно!\n\nТеперь вы можете установить VPN на своё устройство.',
        'keyboard': help_k.HelpKeyboards.help_message()
    },
    'start_menu': {
        'text': '🏠 Главное меню\n\n✅ Статус: Активен\n💰 Подписка: Активна \n ⏰ Пробный период: Истек',
        'keyboard': start_menu.start_menu_keyboard()
    },
    'extend_sub': {
        'text': '💳 Выберите тариф для продления:',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('start_menu')
    },
    'install_vpn': {
        'text': """Выбери платформу:

🤖 Android -  Защити свой Android!  Инструкция по установке VPN на Android телефоны и планшеты.

🍏 IOS/MacOS -  Инструкция для iPhone, iPad и Mac.  Получи инструкцию по установке VPN на устройства Apple.

💻 Windows -  Инструкция для Windows.  Получи подробную инструкцию по установке VPN на платформе Windows.""",
        'keyboard': vpn.VPNInstallKeyboards.choose_platform('start_menu')
    },
    'invite_in_install': {
        'text': '👥 Пригласите друга и получите бонусы!',
        'keyboard': refferal.VPNRefferalKeyboards.invite_menu('install_vpn')
    },
    'buy_key': {
        'text': '💳 Выберите тариф для продления:',
        'keyboard': per_acc.VPNPersAccKeyboards.choose_plan_menu('personal_acc')
    },
    'refferal': {
        'text': '👥 Реферальная программа\n\nПриглашайте друзей и получайте бонусы!',
        'keyboard': refferal.VPNRefferalKeyboards.refferal_menu()
    }
}

# =============================================================================
# СПЕЦИАЛЬНЫЕ ОБРАБОТКИ
# =============================================================================

# Список callback_data, которые требуют переадресации к специалисту поддержки
TO_ME = [
    'help_refferal_not_add',
    'help_period_not_active',
    'help_bank',
    'help_paid_not_active',
    'help_link_inactive',
    'help_links',
    'help_app',
    'help_turn_on'
]

# Платформы для установки
PLATFORM = ['android', 'ios', 'windows']

# Инструкции для платформ
PLATFORM_INSTRUCTIONS = {
    'android': """
🤖 Инструкция для Android:

1. Скачайте приложение  из Google Play
2. Скопируйте ваш ключ доступа из личного кабинета
3. Вставьте ключ в приложение
4. Нажмите "Подключиться"

Готово! VPN активирован.
""",
    'ios': """
🍎 Инструкция для iOS/MacOS:

1. Скачайте приложение  из App Store
2. Скопируйте ваш ключ доступа из личного кабинета
3. Вставьте ключ в приложение
4. Разрешите добавить VPN-конфигурацию
5. Нажмите "Подключиться"

Готово! VPN активирован.
""",
    'windows': """
🪟 Инструкция для Windows:

1. Скачайте  с официального сайта
2. Установите приложение
3. Скопируйте ваш ключ доступа из личного кабинета
4. Вставьте ключ в приложение
5. Нажмите "Подключиться"

Готово! VPN активирован.
"""
}

def get_platform_message(platform: str) -> dict:
    """Возвращает инструкцию для конкретной платформы"""
    return {
        'text': PLATFORM_INSTRUCTIONS.get(platform, 'Платформа не найдена'),
        'keyboard': vpn.VPNInstallKeyboards.platform_chosen()
    }

# =============================================================================
# ОСНОВНАЯ ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ СООБЩЕНИЙ
# =============================================================================

def get_message_by_status(callback_data: str, trial: str = 'never_used', balance: int = 0) -> dict:
    """
    Возвращает сообщение в зависимости от статуса пользователя

    Args:
        callback_data: Название действия (start_menu, install_vpn, etc.)
        trial: Статус пробного периода ('never_used', 'in_progress', 'expired')
        balance: Баланс пользователя

    Returns:
        Словарь с текстом и клавиатурой
    """

    # Обработка специальных случаев
    if callback_data in TO_ME:
        return COMMON_BUTTONS.get('help_to_me')

    if callback_data in PLATFORM:
        return get_platform_message(callback_data)

    # Проверка общих кнопок
    if callback_data in COMMON_BUTTONS:
        return COMMON_BUTTONS[callback_data]

    # Обработка платежа
    if callback_data == 'payment_success':
        return PAID['payment_success']

    # Выбор словаря сообщений по статусу
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

    # Возврат сообщения
    return messages.get(callback_data)

STATUS_VAR = {
    'trial' : {
        'never_used': 'Не использовано',
        'in_progress': 'Используется',
        'expired': 'Истекло'
    },
    'status': {
        '0': 'Не оплачен',
        '>0': 'Оплачен'
    }
}
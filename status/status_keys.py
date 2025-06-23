from keyboards import vpn_keyboards as vpn, start_menu, help_keyboards as help_k, personal_acc as per_acc, refferal
from config_data.config import load_config_help

config = load_config_help('.env')
help_acc = config.tg.tg_user


# =============================================================================
# СООБЩЕНИЯ ДЛЯ НОВЫХ ПОЛЬЗОВАТЕЛЕЙ (БЕЗ ПРОБНОГО ПЕРИОДА)
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
    },
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
# СООБЩЕНИЯ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ С АКТИВНЫМ ПРОБНЫМ ПЕРИОДОМ
# =============================================================================

# =============================================================================
# СООБЩЕНИЯ ДЛЯ ПОЛЬЗОВАТЕЛЕЙ С АКТИВНОЙ ПОДПИСКОЙ
# =============================================================================


# =============================================================================
# ОБЩИЕ СООБЩЕНИЯ (НЕЗАВИСИМО ОТ СТАТУСА)
# =============================================================================




# =============================================================================
# ПОМОЩЬ В ЛИЧНЫЕ СООБЩЕНИЯ
# =============================================================================

TO_ME = ['help_refferal_not_add', 'help_period_not_active', 'help_bank', 'help_paid_not_active', 'help_link_inactive']

# =============================================================================
# ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ СООБЩЕНИЙ
# =============================================================================

def get_message_by_status(callback_data: str, status: str, trial: bool = False) -> dict:
    """
    Возвращает сообщение в зависимости от статуса пользователя

    Args:
        callback_data: Название действия (start_menu, install_vpn, etc.)
        status: Статус пользователя (new, active, expired)
        trial: Активирован ли пробный период

    Returns:
        Словарь с текстом и клавиатурой
    """

    # Сначала ищем в общих сообщениях

    # Выбираем словарь сообщений по статусу
    if status == 'new' and not trial:
        messages = TRAIL_NOT_USED
    elif status == 'new' and trial:
        messages = TRAIL_USED
    elif status == 'active':
        messages = SUBSCRIPTION_ACTIVE
    else:
        messages = TRAIL_NOT_USED  # По умолчанию

    if callback_data in TO_ME:
        message = messages.get('help_to_me')
        return message

    # Ищем конкретное сообщение
    message = messages.get(callback_data)

    return message

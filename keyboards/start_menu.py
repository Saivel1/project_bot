from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


#Пробный период не активирован
def start_menu_keyboard_trail():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Установка VPN", callback_data="install_vpn")],
        [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="personal_acc")],
        [InlineKeyboardButton(text="🎁 Пробный период", callback_data="trial_per")],
        [InlineKeyboardButton(text="👥 Реферальная программа", callback_data="refferal")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])
    return keyboard

# Пробный период не активирован, есть подписка
def start_menu_keyboard_trail_extend():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Установка VPN", callback_data="install_vpn")],
        [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="personal_acc")],
        [InlineKeyboardButton(text="🔄 Продлить подписку", callback_data="extend_sub")],
        [InlineKeyboardButton(text="🎁 Пробный период", callback_data="trial_per")],
        [InlineKeyboardButton(text="👥 Реферальная программа", callback_data="refferal")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])
    return keyboard


#Пробный период активирован
def start_menu_keyboard():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Установка VPN", callback_data="install_vpn")],
        [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="personal_acc")],
        [InlineKeyboardButton(text="🔄 Продлить подписку", callback_data="extend_sub")],
        [InlineKeyboardButton(text="👥 Реферальная программа", callback_data="refferal")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])
    return keyboard

#Пробный период активирован, нет подписки
def start_menu_keyboard_trial_in_progress():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔧 Установка VPN", callback_data="install_vpn")],
        [InlineKeyboardButton(text="👤 Личный кабинет", callback_data="personal_acc")],
        [InlineKeyboardButton(text="💳 Купить подписку", callback_data="buy_key")],
        [InlineKeyboardButton(text="👥 Реферальная программа", callback_data="refferal")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")]
    ])
    return keyboard
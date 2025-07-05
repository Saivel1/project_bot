from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Массив кнопок для КНОПКИ Установить VPN


# Ключа нет
class VPNInstallKeyboards:
    """Класс для управления клавиатурами установки VPN"""

    # ===========================================================
    # Кнопка, когда закончился балланс.
    # ===========================================================
    @staticmethod
    def not_paid_install(back_target):
        """Клавиатура для неоплаченных пользователей"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="buy_key")],
            [InlineKeyboardButton(text="👥 Пригласить друга", callback_data="invite")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="help")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{back_target}")]
        ])
        return keyboard

    # ===========================================================
    # Кнопка, когда баланс 0 и новый пользователь.
    # ===========================================================
    @staticmethod
    def not_paid_install_new(back_target: str):
        """Клавиатура для неоплаченных пользователей"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Пополнить баланс", callback_data="buy_key_in_install")],
            [InlineKeyboardButton(text="👥 Пригласить друга", callback_data="invite_in_install")],
            [InlineKeyboardButton(text="🎁 Активировать пробный период", callback_data="trial_per")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="help_install_vpn")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{back_target}")]
        ])
        return keyboard

    @staticmethod
    def choose_platform(back_target: str):
        """Клавиатура выбора платформы"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🤖 Android", callback_data="android"),
                InlineKeyboardButton(text="🍎 iOS | MacOS", callback_data="ios"),
                InlineKeyboardButton(text="🪟 Windows", callback_data="windows"),
            ],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"{back_target}")],
        ])
        return keyboard

    @staticmethod
    def platform_chosen():
        """Клавиатура после выбора платформы"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="❓ Помощь", callback_data="help_install_vpn")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="install_vpn")]
        ])
        return keyboard
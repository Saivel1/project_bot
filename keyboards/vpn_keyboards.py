from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Массив кнопок для КНОПКИ Установить VPN


# Ключа нет
class VPNInstallKeyboards:
    """Класс для управления клавиатурами установки VPN"""

    @staticmethod
    def not_paid_install():
        """Клавиатура для неоплаченных пользователей"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пополнить баланс", callback_data="buy_key")],
            [InlineKeyboardButton(text="Пригласить друга", callback_data="invite")],
            [InlineKeyboardButton(text="Помощь", callback_data="help")],
            [InlineKeyboardButton(text="Назад", callback_data="back")]
        ])
        return keyboard

    @staticmethod
    def choose_platform(menu_position: str):
        """Клавиатура выбора платформы"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Android", callback_data="android"),
                InlineKeyboardButton(text="IOS | MacOS", callback_data="ios"),
                InlineKeyboardButton(text="Windows", callback_data="windows"),
            ],
            [InlineKeyboardButton(text="Назад", callback_data=f"{menu_position}")],
        ])
        return keyboard

    @staticmethod
    def android_platform():
        """Клавиатура для платформы Android"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Помощь", callback_data="help_install_vpn")],
            [InlineKeyboardButton(text="Назад", callback_data="install_vpn")]
        ])
        return keyboard

    @staticmethod
    def ios_platform():
        """Клавиатура для платформы iOS"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Помощь", callback_data="help")],
            [InlineKeyboardButton(text="Назад", callback_data="install_vpn")]
        ])
        return keyboard

    @staticmethod
    def windows_platform():
        """Клавиатура для платформы Windows"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Помощь", callback_data="help")],
            [InlineKeyboardButton(text="Назад", callback_data="install_vpn")]
        ])
        return keyboard
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Массив кнопок для КНОПКИ Установить VPN


# Ключа нет
class HelpKeyboards:
    """Класс для управления клавиатурами установки VPN"""

    @staticmethod
    def help_main():
        """Клавиатура для неоплаченных пользователей"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Помощь с установкой VPN", callback_data="help_install_vpn")],
            [InlineKeyboardButton(text="Помощь с оплатой и личный кабинетом", callback_data="help_per_acc")],
            [InlineKeyboardButton(text="Помощь с пробным периодом", callback_data="help_period")],
            [InlineKeyboardButton(text="Помощь с реферальной программой", callback_data="help_refferal")],
            [InlineKeyboardButton(text="Назад", callback_data="start_menu")]
        ])
        return keyboard

    # Меню помощи с установкой VPN
    @staticmethod
    def help_install_vpn():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Ссылки не работают", callback_data="help_links")],
            [InlineKeyboardButton(text="Приложение не работает", callback_data="help_app")],
            [InlineKeyboardButton(text="VPN не включается", callback_data="help_turn_on")],
            [InlineKeyboardButton(text="Назад", callback_data="help")],
        ])
        return keyboard

    # Меню помощи с оплатой и личным кабинетом
    @staticmethod
    def help_per_acc():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Нет моего банка", callback_data="help_bank")],
            [InlineKeyboardButton(text="Деньги списались, но нет подписки", callback_data="help_paid_not_active")],
            [InlineKeyboardButton(text="Не могу перейти по ссылки", callback_data="help_link_inactive")],
            [InlineKeyboardButton(text="Назад", callback_data="help")],
        ])
        return keyboard

    # Меню помощи с пробным периодом
    @staticmethod
    def help_period():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пробный период не активировался", callback_data="help_period_not_active")],
            [InlineKeyboardButton(text="Назад", callback_data="help")],
        ])
        return keyboard

    # Меню помощи с реферальной программой
    @staticmethod
    def help_refferal():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="За друга не начислили дни", callback_data="help_refferal_not_add")],
            [InlineKeyboardButton(text="Назад", callback_data="help")],
        ])
        return keyboard
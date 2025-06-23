from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Массив кнопок для КНОПКИ Установить VPN


# Ключа нет
class VPNPersAccKeyboards:
    """Класс для управления клавиатурами установки VPN"""

    @staticmethod
    def personal_acc():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пополнить балланс", callback_data="buy_key")],
            [InlineKeyboardButton(text="Изменить email", callback_data="change_email")],
            [InlineKeyboardButton(text="Помощь", callback_data="help_per_acc_in_per_acc")],
            [InlineKeyboardButton(text="Назад", callback_data="start_menu")]
        ])
        return keyboard

    # ===========================================================
    # Кнопки когда новый пользователь.
    # ===========================================================
    @staticmethod
    def personal_acc_new():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пополнить балланс", callback_data="buy_key")],
            [InlineKeyboardButton(text="Активировать пробный период", callback_data="trial_per")],
            [InlineKeyboardButton(text="Помощь", callback_data="help_per_acc_in_per_acc")],
            [InlineKeyboardButton(text="Назад", callback_data="start_menu")]
        ])
        return keyboard

    @staticmethod
    def change_email():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="personal_acc")]
        ])
        return keyboard

    # ===========================================================
    # Кнопки пополнения балланса, когда новый пользователь
    # ===========================================================
    @staticmethod
    def choose_plan_menu_new(back_target: str):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1 мес. | 50 руб.", callback_data="to_pay_month")],
            [InlineKeyboardButton(text="3 мес. | 150 руб.", callback_data="to_pay_3_months")],
            [InlineKeyboardButton(text="6 мес. | 300 руб.", callback_data="to_pay_6_months")],
            [InlineKeyboardButton(text="1 год. | 600 руб.", callback_data="to_pay_year")],
            [InlineKeyboardButton(text="Активировать пробный период", callback_data="trial_per")],
            [InlineKeyboardButton(text="Помощь", callback_data="help_per_acc")],
            [InlineKeyboardButton(text="Назад", callback_data=f"{back_target}")],
        ])
        return keyboard

    @staticmethod
    def choose_plan_menu(back_target: str):
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="1 мес. | 50 руб.", callback_data="to_pay_month")],
            [InlineKeyboardButton(text="3 мес. | 150 руб.", callback_data="to_pay_3_months")],
            [InlineKeyboardButton(text="6 мес. | 300 руб.", callback_data="to_pay_6_months")],
            [InlineKeyboardButton(text="1 год. | 600 руб.", callback_data="to_pay_year")],
            [InlineKeyboardButton(text="Помощь", callback_data="help_per_acc")],
            [InlineKeyboardButton(text="Назад", callback_data=f"{back_target}")],
        ])
        return keyboard

    @staticmethod
    def error_payment():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Личный кабинет", callback_data="personal_acc")],
            [InlineKeyboardButton(text="Помощь", callback_data="help_per_acc")],
            [InlineKeyboardButton(text="Назад", callback_data="buy_key")]
        ])
        return keyboard

    @staticmethod
    def changing_nickname():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Продолжить", callback_data="accept_ch_acc")],
            [InlineKeyboardButton(text="Отменить", callback_data="decline_ch_acc")],
            [InlineKeyboardButton(text="Назад", callback_data="personal_acc")]
        ])
        return keyboard
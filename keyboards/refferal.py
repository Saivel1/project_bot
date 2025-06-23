from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class VPNRefferalKeyboards:

    @staticmethod
    def refferal_menu():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Пригласить друга", callback_data="invite")],
            [InlineKeyboardButton(text="Помощь", callback_data="help_refferal")],
            [InlineKeyboardButton(text="Назад", callback_data="start_menu")]
        ])
        return keyboard

    @staticmethod
    def invite_menu():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Назад", callback_data="refferal")]
        ])
        return keyboard
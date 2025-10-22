from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

class VPNSubAndKeys:

    @staticmethod
    def sub_and_keys():
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🖼️ Digital", callback_data="digital")],
            [InlineKeyboardButton(text="🌎 World", callback_data="world")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="start_menu")]
        ])
        return keyboard

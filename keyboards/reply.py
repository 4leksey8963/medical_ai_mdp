from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_keyboard() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="ℹ️ О боте"),
        KeyboardButton(text="🔍 Поиск")
    )
    builder.row(KeyboardButton(text="⚙️ Настройки"))
    return builder.as_markup(resize_keyboard=True)
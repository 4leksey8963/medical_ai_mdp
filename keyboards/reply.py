from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def main_keyboard() -> ReplyKeyboardMarkup:
    """Основная клавиатура для зарегистрированных пользователей."""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📄 Прикрепить анализы"), 
        KeyboardButton(text="ℹ️ О боте")
    )
    # Кнопка "Мой профиль" пока может быть заглушкой или вести к информации
    builder.row(KeyboardButton(text="⚙️ Мой профиль")) 
    builder.row(KeyboardButton(text="🔄 Начать заново (сброс)")) # Новая кнопка
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Выберите действие...")

def registration_start_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура для начала регистрации."""
    builder = ReplyKeyboardBuilder()
    builder.button(text="📝 Зарегистрироваться")
    return builder.as_markup(resize_keyboard=True, input_field_placeholder="Нажмите, чтобы зарегистрироваться")
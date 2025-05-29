# keyboards/inline.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
import pathlib 
import os

# --- Определение URL для WebApp ---
# Сначала пытаемся определить путь к form.html относительно текущего файла
# Это предполагает, что inline.py находится в /keyboards, а form.html в корне проекта
try:
    current_file_path = pathlib.Path(__file__).resolve()
    project_root = current_file_path.parent.parent 
    form_html_path = project_root / "form.html"
except NameError: 
    project_root = pathlib.Path(os.getcwd())
    form_html_path = project_root / "form.html"

# ЗАМЕНИТЕ ЭТОТ URL НА ВАШ РЕАЛЬНЫЙ HTTPS URL С GITHUB PAGES ИЛИ ДРУГОГО ХОСТИНГА
# ЕСЛИ ВЫ РЕШИТЕ ИСПОЛЬЗОВАТЬ ХОСТИНГ ВМЕСТО ЛОКАЛЬНОГО ФАЙЛА
# Пример для GitHub Pages: "https://yourusername.github.io/your-repo-name/form.html"
# Для примера использую ваш URL, убедитесь, что он корректен и form.html там есть
HOSTED_FORM_URL = "https://tolmachevski.github.io/form.html" 

FORM_WEBAPP_URL = HOSTED_FORM_URL 

print(f"INFO: URL для WebApp формы: {FORM_WEBAPP_URL}")

def data_input_method_inline_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора метода ввода данных (PDF или WebApp форма)."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📄 Загрузить PDF", callback_data="input_method_pdf")
    builder.button(text="📝 Заполнить форму онлайн", web_app=WebAppInfo(url=FORM_WEBAPP_URL))
    builder.button(text="Отмена", callback_data="cancel_analysis_input")
    builder.adjust(1)
    return builder.as_markup()

def confirm_analysis_data_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения или редактирования распознанных данных."""
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Все верно", callback_data="confirm_data_correct")
    builder.button(text="✏️ Редактировать", callback_data="confirm_data_edit_manual") 
    builder.button(text="🔄 Ввести другие данные", callback_data="force_reload_data_source") 
    builder.adjust(2,1) 
    return builder.as_markup()

def after_edit_prompt_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после запроса на редактирование, предлагает показать текст для копирования."""
    builder = InlineKeyboardBuilder()
    builder.button(text="📋 Показать текст для копирования", callback_data="resend_editable_text")
    builder.button(text="⬅️ Назад (отмена редактирования)", callback_data="cancel_edit_and_return")
    builder.adjust(1)
    return builder.as_markup()

def after_llm_result_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после получения заключения от LLM."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Проанализировать другие данные", callback_data="analyze_new_data")
    builder.button(text="👤 Изменить профиль / Перерегистрация", callback_data="reregister_profile")
    builder.adjust(1)
    return builder.as_markup()

def gender_selection_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🚹 Мужской", callback_data="gender_male")
    builder.button(text="🚺 Женский", callback_data="gender_female")
    builder.adjust(2)
    return builder.as_markup()

def medical_history_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    diseases = {
        "diabetes": "Диабет", "hypertension": "Гипертония",
        "thyroid_disorders": "Заболевания щитовидной железы",
        "anemia": "Анемия", "none": "Нет хронических заболеваний"
    }
    for code, name in diseases.items():
        builder.button(text=name, callback_data=f"med_hist_{code}")
    builder.button(text="➡️ Другое / Ввести текстом", callback_data="med_hist_skip_other")
    builder.adjust(1)
    return builder.as_markup()

def habits_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    habits_options = {
        "smoking": "🚬 Курение", "alcohol": "🍷 Алкоголь (регулярно)",
        "none": "✅ Нет зависимостей"
    }
    for code, name in habits_options.items():
        builder.button(text=name, callback_data=f"habit_{code}")
    builder.button(text="➡️ Другое / Ввести текстом", callback_data="habit_skip_other")
    builder.adjust(1)
    return builder.as_markup()

def diet_features_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    diet_options = {
        "vegetarian": "🥦 Вегетарианство", "vegan": "🥕 Веганство", "keto": "🥩 Кето-диета",
        "gluten_free": "🚫 Без глютена", "lactose_free": "🥛 Без лактозы",
        "none": "🍽️ Обычное питание"
    }
    for code, name in diet_options.items():
        builder.button(text=name, callback_data=f"diet_{code}")
    builder.button(text="➡️ Другое / Ввести текстом", callback_data="diet_skip_other")
    builder.adjust(1)
    return builder.as_markup()

def skip_keyboard(next_step_callback_data: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➡️ Далее", callback_data=next_step_callback_data)
    return builder.as_markup()

def cancel_action_keyboard(callback_data: str = "cancel_current_action") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="Отмена", callback_data=callback_data)
    return builder.as_markup()
# handlers/commands.py
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import os # для удаления файла профиля

# Импорты ваших модулей
from keyboards.reply import registration_start_keyboard, main_keyboard
from keyboards.inline import gender_selection_keyboard, data_input_method_inline_keyboard 
from states.registration_states import RegistrationStates, AnalysisStates 
from utils.file_helpers import load_user_data_from_json, PERSON_DATA_DIR 
from config import bot 

router = Router()

async def safe_delete_message(chat_id: int, message_id: int):
    """Безопасное удаление сообщения."""
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        pass

async def perform_reregistration(message_or_callback: types.Message | types.CallbackQuery, state: FSMContext):
    """Общая функция для логики сброса профиля и начала перерегистрации."""
    user_id = message_or_callback.from_user.id
    
    await state.clear() # Очищаем любое текущее состояние FSM
    
    user_profile_path = PERSON_DATA_DIR / str(user_id) / "profile.json"
    delete_feedback_message = ""
    if user_profile_path.exists():
        try:
            user_profile_path.unlink() # Удаляем файл профиля
            delete_feedback_message = "Ваш предыдущий профиль был успешно сброшен.\n"
            print(f"Профиль для user_id {user_id} удален.")
        except OSError as e:
            print(f"Ошибка удаления файла профиля для user_id {user_id}: {e}")
            delete_feedback_message = "Не удалось полностью сбросить ваш предыдущий профиль, но вы можете пройти регистрацию заново.\n"
    else:
        delete_feedback_message = "Начинаем процесс регистрации...\n" # Если профиля и не было

    start_message_text = (
        f"{delete_feedback_message}"
        "🌟 Я — виртуальный помощник для заботы о вашем здоровье! 🌟\n"
        "🔍 Разработан для анализа медицинских данных пациента и результатов лабораторных исследований с целью формирования индивидуальных рекомендаций по оздоровлению.\n"
        "📊 На основе приложенных документов я могу:\n"
        "⚠️ Выявить отклонения от нормы\n"
        "💡 Предложить стратегии коррекции состояния организма\n"
        "🥗 Разработать персонализированный план питания, соответствующий вашим физиологическим особенностям и потребностям.\n"
        "ℹ️ Мои рекомендации носят общий характер и не заменяют консультацию врача 👨‍⚕️👩‍⚕️.\n"
        "💙 Моя цель — помочь вам лучше понимать своё здоровье и принимать осознанные решения в уходе за собой!\n\n"
        "Для начала работы и получения персонализированных рекомендаций, пожалуйста, пройдите короткую регистрацию."
    )
    
    # Отправляем сообщение от имени бота
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(start_message_text, reply_markup=registration_start_keyboard())
    elif isinstance(message_or_callback, types.CallbackQuery):
        await bot.send_message(chat_id=user_id, text=start_message_text, reply_markup=registration_start_keyboard())
        if message_or_callback.message: # Удаляем сообщение с инлайн кнопкой, если это был колбэк
             await safe_delete_message(message_or_callback.message.chat.id, message_or_callback.message.message_id)
             
    await state.set_state(RegistrationStates.waiting_for_registration_start)


@router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = load_user_data_from_json(user_id)
    is_registered = user_data is not None
    current_fsm_state = await state.get_state() 
    if current_fsm_state is not None:
        await state.clear() 

    if is_registered:
        reg_data = user_data.get("registration_data", {})
        first_name_to_greet = reg_data.get("first_name") or user_data.get("first_name") or message.from_user.first_name
        
        await message.answer(
            f"С возвращением, {first_name_to_greet}!\n"
            "Готов помочь вам с анализом медицинских данных.",
            reply_markup=main_keyboard() 
        )
    else:
        # Если не зарегистрирован, вызываем логику перерегистрации, которая отправит приветствие
        await perform_reregistration(message, state)


@router.message(Command("cancel"))
@router.message(F.text.casefold() == "отмена")
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных действий для отмены.")
        return
    await state.clear()
    user_data = load_user_data_from_json(message.from_user.id)
    reply_markup_after_cancel = main_keyboard() if user_data else registration_start_keyboard()
    await message.answer(
        "Действие отменено.",
        reply_markup=reply_markup_after_cancel
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    help_text = (
        "ℹ️ **Справочная информация:**\n"
        "Для начала работы со мной, если вы еще не зарегистрированы, пройдите короткую регистрацию после команды /start\\.\n"
        "После регистрации вы сможете прикреплять анализы \\(PDF или заполнить форму\\) для получения рекомендаций\\.\n\n"
        "Основные команды:\n"
        "/start \\- начать работу с ботом / пройти регистрацию\\.\n"
        "/cancel \\- отменить текущее действие \\(например, регистрацию или ввод анализов\\)\\.\n"
        "/reregister или кнопка '🔄 Начать заново (сброс)' \\- пройти регистрацию заново, ваши предыдущие данные профиля будут удалены\\."
    )
    await message.answer(help_text, parse_mode="MarkdownV2")


@router.message(F.text == "📄 Прикрепить анализы")
async def choose_analysis_input_method(message: types.Message, state: FSMContext):
    user_data = load_user_data_from_json(message.from_user.id)
    if not user_data:
        await message.answer(
            "Пожалуйста, сначала пройдите регистрацию. Для этого нажмите /start.",
            reply_markup=registration_start_keyboard()
            )
        # await state.set_state(RegistrationStates.waiting_for_registration_start) # Не нужно, cmd_start это сделает
        return # cmd_start перенаправит на регистрацию, если пользователь не зарегистрирован
    
    # Если пользователь зарегистрирован, предлагаем выбор метода
    # Убедимся, что мы не в середине другого процесса
    current_fsm_state = await state.get_state()
    if current_fsm_state is not None and not current_fsm_state.startswith("AnalysisStates:"):
        await state.clear() # Очищаем другие состояния перед началом анализа

    await message.answer(
        "Как вы хотите предоставить данные анализов?",
        reply_markup=data_input_method_inline_keyboard()
    )
    await state.set_state(AnalysisStates.waiting_input_method)


@router.message(Command("reregister"))
async def cmd_reregister(message: types.Message, state: FSMContext):
    await perform_reregistration(message, state)

@router.message(F.text == "🔄 Начать заново (сброс)")
async def handle_reregister_button(message: types.Message, state: FSMContext):
    # Можно добавить инлайн-кнопки для подтверждения Да/Нет
    # builder = InlineKeyboardBuilder()
    # builder.button(text="Да, сбросить профиль", callback_data="confirm_reregister_yes")
    # builder.button(text="Нет, отмена", callback_data="confirm_reregister_no")
    # await message.answer("Вы уверены, что хотите сбросить все данные профиля и начать регистрацию заново?", 
    #                      reply_markup=builder.as_markup())
    # await state.set_state(SomeStateForReregisterConfirm) # Потребуется новое состояние
    # Пока делаем прямой сброс:
    await message.reply("Выполняю сброс и начинаю регистрацию заново...")
    await perform_reregistration(message, state)

# Пример заглушки для кнопки "Мой профиль"
@router.message(F.text == "⚙️ Мой профиль")
async def handle_my_profile_button(message: types.Message, state: FSMContext):
    user_data = load_user_data_from_json(message.from_user.id)
    if not user_data:
        await message.answer(
            "Вы еще не зарегистрированы. Пожалуйста, начните с команды /start.",
            reply_markup=registration_start_keyboard()
        )
        await state.set_state(RegistrationStates.waiting_for_registration_start)
        return

    reg_data = user_data.get("registration_data", {})
    profile_info = [f"👤 **Ваш профиль**"]
    profile_info.append(f"ID: `{message.from_user.id}`")
    if message.from_user.username:
        profile_info.append(f"Юзернейм: @{message.from_user.username}")
    
    profile_info.append(f"\n📋 **Данные анкеты:**")
    gender_map = {"male": "Мужской", "female": "Женский"}
    profile_info.append(f"Пол: {gender_map.get(reg_data.get('gender'), 'не указан')}")
    profile_info.append(f"Возраст: {reg_data.get('age', 'не указан')} лет")
    profile_info.append(f"Вес: {reg_data.get('weight', 'не указан')} кг")
    profile_info.append(f"Рост: {reg_data.get('height', 'не указан')} см")

    med_hist_list = reg_data.get('medical_history_list', [])
    med_hist_text = reg_data.get('medical_history_text', '')
    chronic_text = "не указаны"
    combined_hist = []
    if med_hist_list and "none" not in med_hist_list: combined_hist.extend(med_hist_list)
    if med_hist_text and med_hist_text.lower() not in ["нет", "", "none"]: combined_hist.append(med_hist_text)
    if combined_hist: chronic_text = "; ".join(combined_hist)
    elif "none" in med_hist_list: chronic_text = "отсутствуют"
    profile_info.append(f"Хронические заболевания: {chronic_text}")

    # ... (аналогично для привычек, диеты, сна) ...

    profile_info.append(f"\nДля изменения данных используйте кнопку '🔄 Начать заново (сброс)' или команду /reregister.")

    await message.answer("\n".join(profile_info), parse_mode="Markdown")
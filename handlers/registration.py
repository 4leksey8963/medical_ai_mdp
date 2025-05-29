# handlers/registration.py
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from states.registration_states import RegistrationStates, AnalysisStates 
from keyboards.inline import (
    gender_selection_keyboard, # Добавлен импорт, так как используется
    medical_history_keyboard, habits_keyboard,
    diet_features_keyboard, skip_keyboard,
    data_input_method_inline_keyboard 
)
from utils.file_helpers import save_user_data_to_json
from config import bot

router = Router()

async def safe_delete_message(chat_id: int, message_id: int):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        pass

@router.message(RegistrationStates.waiting_for_registration_start, F.text == "📝 Зарегистрироваться")
async def process_registration_start_button(message: types.Message, state: FSMContext):
    try:
        await message.delete()
    except TelegramBadRequest:
        pass
    await message.answer("Отлично! Давайте начнем.", reply_markup=types.ReplyKeyboardRemove())
    inline_keyboard_msg = await message.answer(
        "Пожалуйста, укажите ваш пол:",
        reply_markup=gender_selection_keyboard() 
    )
    await state.set_state(RegistrationStates.waiting_for_gender)


@router.callback_query(RegistrationStates.waiting_for_gender, F.data.startswith("gender_"))
async def process_gender_selection(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    gender = callback.data.split("_")[1]
    await state.update_data(gender=gender)
    if callback.message:
        await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    new_question_msg = await callback.message.answer(
        f"Ваш пол: {'Мужской' if gender == 'male' else 'Женский'}.\n"
        "Теперь, пожалуйста, укажите ваш возраст (полных лет, только цифры):"
    )
    await state.update_data(last_bot_message_id=new_question_msg.message_id)
    await state.set_state(RegistrationStates.waiting_for_age)

@router.message(RegistrationStates.waiting_for_age)
async def process_age(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    last_bot_msg_id = user_data.get("last_bot_message_id")
    if not message.text or not message.text.isdigit():
        await message.answer("Пожалуйста, введите возраст цифрами (например, 30).")
        await safe_delete_message(message.chat.id, message.message_id)
        return
    age = int(message.text)
    if not (5 <= age <= 120):
        await message.answer("Пожалуйста, введите корректный возраст (от 5 до 120 лет).")
        await safe_delete_message(message.chat.id, message.message_id)
        return
    if last_bot_msg_id:
        await safe_delete_message(message.chat.id, last_bot_msg_id)
    await safe_delete_message(message.chat.id, message.message_id)
    await state.update_data(age=age)
    new_question_msg = await message.answer(
        f"Ваш возраст: {age} лет.\nТеперь укажите ваш вес в килограммах (например, 70 или 70.5):"
    )
    await state.update_data(last_bot_message_id=new_question_msg.message_id)
    await state.set_state(RegistrationStates.waiting_for_weight)

@router.message(RegistrationStates.waiting_for_weight)
async def process_weight(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    last_bot_msg_id = user_data.get("last_bot_message_id")
    try:
        weight_str = message.text.replace(',', '.')
        weight = float(weight_str)
        if not (20 <= weight <= 300): raise ValueError("Некорректный вес")
    except ValueError:
        await message.answer("Пожалуйста, введите вес корректно цифрами (например, 70 или 70.5).")
        await safe_delete_message(message.chat.id, message.message_id)
        return
    if last_bot_msg_id:
        await safe_delete_message(message.chat.id, last_bot_msg_id)
    await safe_delete_message(message.chat.id, message.message_id)
    await state.update_data(weight=weight)
    new_question_msg = await message.answer(
        f"Ваш вес: {weight} кг.\nУкажите ваш рост в сантиметрах (например, 175):"
    )
    await state.update_data(last_bot_message_id=new_question_msg.message_id)
    await state.set_state(RegistrationStates.waiting_for_height)

@router.message(RegistrationStates.waiting_for_height)
async def process_height(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    last_bot_msg_id = user_data.get("last_bot_message_id")
    if not message.text or not message.text.isdigit():
        await message.answer("Пожалуйста, введите рост цифрами в сантиметрах (например, 175).")
        await safe_delete_message(message.chat.id, message.message_id)
        return
    height = int(message.text)
    if not (100 <= height <= 250):
        await message.answer("Пожалуйста, введите корректный рост (от 100 до 250 см).")
        await safe_delete_message(message.chat.id, message.message_id)
        return
    if last_bot_msg_id:
        await safe_delete_message(message.chat.id, last_bot_msg_id)
    await safe_delete_message(message.chat.id, message.message_id)
    await state.update_data(height=height)
    new_question_msg = await message.answer(
        f"Ваш рост: {height} см.\n"
        "Теперь выберите из списка или опишите вашу медицинскую историю (хронические заболевания, если есть, которые могут влиять на анализ крови). "
        "Если нет, выберите соответствующий пункт или пропустите.",
        reply_markup=medical_history_keyboard()
    )
    await state.update_data(last_bot_message_id=new_question_msg.message_id)
    await state.set_state(RegistrationStates.waiting_for_medical_history)

@router.callback_query(RegistrationStates.waiting_for_medical_history, F.data.startswith("med_hist_"))
async def process_medical_history_choice(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    choice = callback.data.replace("med_hist_", "")
    if callback.message:
        await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    if choice == "skip_other":
        new_question_msg = await callback.message.answer(
            "Пожалуйста, введите вашу медицинскую историю текстом или напишите 'нет', если ничего нет."
        )
        await state.update_data(last_bot_message_id=new_question_msg.message_id)
    else:
        user_data_state = await state.get_data()
        current_history = user_data_state.get("medical_history_list", [])
        if choice == "none":
            current_history = ["none"]
        elif choice not in current_history:
             current_history.append(choice)
             if "none" in current_history: current_history.remove("none") 

        await state.update_data(medical_history_list=current_history)
        
        selected_text_display = "не указано"
        if current_history == ["none"]:
            selected_text_display = "нет хронических заболеваний"
        elif current_history:
            selected_text_display = ", ".join(current_history) 
        
        new_question_msg = await callback.message.answer(
            f"Выбранная мед. история: {selected_text_display}.\n"
            "Если хотите добавить еще или изменить, введите текстом. Или нажмите 'Далее'.",
            reply_markup=skip_keyboard("next_to_habits")
        )
        await state.update_data(last_bot_message_id=new_question_msg.message_id)

@router.message(RegistrationStates.waiting_for_medical_history)
async def process_medical_history_text(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    last_bot_msg_id = user_data.get("last_bot_message_id")
    if last_bot_msg_id:
        await safe_delete_message(message.chat.id, last_bot_msg_id)
    await safe_delete_message(message.chat.id, message.message_id)
    await state.update_data(medical_history_text=message.text) 
    new_question_msg = await message.answer(
        f"Медицинская история принята: {message.text}.\n"
        "Есть ли у вас зависимости (курение, алкоголь)?",
        reply_markup=habits_keyboard()
    )
    await state.update_data(last_bot_message_id=new_question_msg.message_id)
    await state.set_state(RegistrationStates.waiting_for_habits)

@router.callback_query(RegistrationStates.waiting_for_medical_history, F.data == "next_to_habits")
async def process_next_to_habits(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.message:
        await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    new_question_msg = await callback.message.answer(
        "Медицинская история сохранена.\n"
        "Есть ли у вас зависимости (курение, алкоголь)?",
        reply_markup=habits_keyboard()
    )
    await state.update_data(last_bot_message_id=new_question_msg.message_id)
    await state.set_state(RegistrationStates.waiting_for_habits)

@router.callback_query(RegistrationStates.waiting_for_habits, F.data.startswith("habit_"))
async def process_habits_choice(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    choice = callback.data.replace("habit_", "")
    if callback.message: await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    if choice == "skip_other":
        new_msg = await callback.message.answer("Пожалуйста, опишите ваши зависимости текстом или напишите 'нет'.")
        await state.update_data(last_bot_message_id=new_msg.message_id)
    else:
        user_data_state = await state.get_data()
        current_habits = user_data_state.get("habits_list", [])
        if choice == "none":
            current_habits = ["none"]
        elif choice not in current_habits:
            current_habits.append(choice)
            if "none" in current_habits: current_habits.remove("none")
        await state.update_data(habits_list=current_habits)
        selected_text = ("нет" if "none" in current_habits else (", ".join(current_habits) if current_habits else "не указано"))
        new_msg = await callback.message.answer(
            f"Выбранные зависимости: {selected_text}.\n"
            "Введите текст или нажмите 'Далее'.", reply_markup=skip_keyboard("next_to_diet"))
        await state.update_data(last_bot_message_id=new_msg.message_id)

@router.message(RegistrationStates.waiting_for_habits)
async def process_habits_text(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    last_bot_msg_id = user_data.get("last_bot_message_id")
    if last_bot_msg_id: await safe_delete_message(message.chat.id, last_bot_msg_id)
    await safe_delete_message(message.chat.id, message.message_id)
    await state.update_data(habits_text=message.text)
    new_msg = await message.answer(f"Зависимости: {message.text}.\nОсобенности рациона?", reply_markup=diet_features_keyboard())
    await state.update_data(last_bot_message_id=new_msg.message_id)
    await state.set_state(RegistrationStates.waiting_for_diet_features)

@router.callback_query(RegistrationStates.waiting_for_habits, F.data == "next_to_diet")
async def process_next_to_diet(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.message: await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    new_msg = await callback.message.answer("Зависимости сохранены.\nОсобенности рациона?", reply_markup=diet_features_keyboard())
    await state.update_data(last_bot_message_id=new_msg.message_id)
    await state.set_state(RegistrationStates.waiting_for_diet_features)

@router.callback_query(RegistrationStates.waiting_for_diet_features, F.data.startswith("diet_"))
async def process_diet_choice(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    choice = callback.data.replace("diet_", "")
    if callback.message: await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    if choice == "skip_other":
        new_msg = await callback.message.answer("Пожалуйста, опишите особенности вашего рациона или напишите 'нет'.")
        await state.update_data(last_bot_message_id=new_msg.message_id)
    else:
        user_data_state = await state.get_data()
        current_diet = user_data_state.get("diet_list", [])
        if choice == "none":
            current_diet = ["none"]
        elif choice not in current_diet:
            current_diet.append(choice)
            if "none" in current_diet: current_diet.remove("none")
        await state.update_data(diet_list=current_diet)
        selected_text = ("обычное питание" if "none" in current_diet else (", ".join(current_diet) if current_diet else "не указано"))
        new_msg = await callback.message.answer(
            f"Особенности рациона: {selected_text}.\n"
            "Введите текст или нажмите 'Далее'.", reply_markup=skip_keyboard("next_to_sleep"))
        await state.update_data(last_bot_message_id=new_msg.message_id)

@router.message(RegistrationStates.waiting_for_diet_features)
async def process_diet_text(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    last_bot_msg_id = user_data.get("last_bot_message_id")
    if last_bot_msg_id: await safe_delete_message(message.chat.id, last_bot_msg_id)
    await safe_delete_message(message.chat.id, message.message_id)
    await state.update_data(diet_text=message.text)
    new_msg = await message.answer(f"Рацион: {message.text}.\nОпишите ваш режим сна:")
    await state.update_data(last_bot_message_id=new_msg.message_id)
    await state.set_state(RegistrationStates.waiting_for_sleep_pattern)

@router.callback_query(RegistrationStates.waiting_for_diet_features, F.data == "next_to_sleep")
async def process_next_to_sleep(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.message: await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    new_msg = await callback.message.answer("Рацион сохранен.\nОпишите ваш режим сна:")
    await state.update_data(last_bot_message_id=new_msg.message_id)
    await state.set_state(RegistrationStates.waiting_for_sleep_pattern)

@router.message(RegistrationStates.waiting_for_sleep_pattern)
async def process_sleep_pattern(message: types.Message, state: FSMContext):
    user_data_from_state = await state.get_data()
    last_bot_msg_id = user_data_from_state.get("last_bot_message_id")
    if last_bot_msg_id:
        await safe_delete_message(message.chat.id, last_bot_msg_id)
    await safe_delete_message(message.chat.id, message.message_id)
    await state.update_data(sleep_pattern=message.text)
    
    final_user_data = await state.get_data()
    final_user_data.pop("last_bot_message_id", None) # Удаляем служебное поле
    
    user_profile_data = {
        "user_id": message.from_user.id,
        "username": message.from_user.username,
        "first_name": message.from_user.first_name,
        "last_name": message.from_user.last_name,
        "registration_data": final_user_data
    }
    
    save_status_message = "Ваши данные успешно сохранены." if save_user_data_to_json(message.from_user, user_profile_data) else "Произошла ошибка при сохранении ваших данных."
    
    await state.clear() 

    summary_text = f"✅ Регистрация успешно завершена!\n{save_status_message}\n\n"
    # summary_text += "Теперь выберите способ предоставления данных для анализа:" # Убрал дублирование

    await message.answer(summary_text, reply_markup=types.ReplyKeyboardRemove()) 
    await message.answer(
        "Как вы хотите предоставить данные анализов?", 
        reply_markup=data_input_method_inline_keyboard()
    )
    await state.set_state(AnalysisStates.waiting_input_method)
# handlers/analysis_handler.py
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
import asyncio
import json
import re

from states.registration_states import AnalysisStates, RegistrationStates 
from utils.pdf_text_extractor import extract_text_from_pdf_bytes_async
from utils.analysis_data_parser import save_parsed_analysis_to_json
from utils.llm_service import llm_parse_medical_text_to_json, get_llm_completion
from keyboards.inline import (
    data_input_method_inline_keyboard, 
    confirm_analysis_data_keyboard,
    after_edit_prompt_keyboard,
    after_llm_result_keyboard 
)
from config import bot
from utils.file_helpers import load_user_data_from_json
# Импортируем функцию perform_reregistration
from handlers.commands import perform_reregistration 

router = Router()

async def safe_delete_message(chat_id: int, message_id: int):
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except TelegramBadRequest:
        pass

DISPLAY_NAMES_MAP_ANALYSIS = {
    "hemoglobin": "Гемоглобин (Hb)", "rbc": "Эритроциты (RBC)", "hematocrit": "Гематокрит (HCT)", 
    "mcv": "Средний объем эритроцита (MCV)", "mch": "Среднее содержание Hb в эритроците (MCH)", 
    "mchc": "Средняя концентрация Hb в эритроците (MCHC)", "rdw_cv": "Гетерогенность эритроцитов (RDW-CV %)",
    "rdw_sd": "Гетерогенность эритроцитов (RDW-SD фл)", "nrbc_abs": "Нормобласты (NRBC абс.)",
    "nrbc_pct": "Нормобласты (NRBC %)", "macrocytes_pct": "Макроциты (MacroR %)",
    "microcytes_pct": "Микроциты (MicroR %)", "color_index": "Цветовой показатель",
    "plt": "Тромбоциты (PLT)", "pct": "Тромбокрит (PCT %)", "mpv": "Средний объем тромбоцитов (MPV фл)",
    "pdw": "Гетерогенность тромбоцитов (PDW фл)", "p_lcr": "Коэффициент крупных тромбоцитов (P-LCR %)",
    "wbc": "Лейкоциты (WBC)", "neutrophils_abs": "Нейтрофилы (NEU абс.)",
    "neutrophils_pct": "Нейтрофилы (NEU %)", "band_neutrophils_abs": "Палочкоядерные нейтрофилы (абс.)",
    "band_neutrophils_pct": "Палочкоядерные нейтрофилы (%)", "seg_neutrophils_abs": "Сегментоядерные нейтрофилы (абс.)",
    "seg_neutrophils_pct": "Сегментоядерные нейтрофилы (%)", "eosinophils_abs": "Эозинофилы (EOS абс.)",
    "eosinophils_pct": "Эозинофилы (EOS %)", "basophils_abs": "Базофилы (BAS абс.)",
    "basophils_pct": "Базофилы (BAS %)", "monocytes_abs": "Моноциты (MON абс.)",
    "monocytes_pct": "Моноциты (MON %)", "lymphocytes_abs": "Лимфоциты (LYM абс.)",
    "lymphocytes_pct": "Лимфоциты (LYM %)", "ig_abs": "Незрелые гранулоциты (IG абс.)",
    "ig_pct": "Незрелые гранулоциты (IG %)", "re_lymp_abs": "Реактивные лимфоциты (RE-LYMP абс.)",
    "re_lymp_pct": "Реактивные лимфоциты (RE-LYMP %)", "as_lymp_abs": "Плазматические клетки (AS-LYMP абс.)",
    "as_lymp_pct": "Плазматические клетки (AS-LYMP %)", "neut_ri": "Интенсивность реактивности нейтрофилов (NEUT-RI)",
    "neut_gi": "Показатель гранулярности нейтрофилов (NEUT-GI)", "esr": "СОЭ (по Вестергрену)",
    "protein_total": "Общий белок", "albumin": "Альбумин", "glucose": "Глюкоза",
    "cholesterol_total": "Холестерин общий", "hdl": "ЛПВП (HDL)", "ldl": "ЛПНП (LDL)",
    "triglycerides": "Триглицериды", "bilirubin_total": "Билирубин общий",
    "bilirubin_direct": "Билирубин прямой", "bilirubin_indirect": "Билирубин непрямой",
    "alt": "АЛТ (ALT)", "ast": "АСТ (AST)", "creatinine": "Креатинин",
    "urea": "Мочевина", "potassium": "Калий (K)", "sodium": "Натрий (Na)", "chloride": "Хлор (Cl)",
    "urine_color": "Цвет (мочи)", "urine_clarity": "Прозрачность (мочи)", 
    "urine_ph": "Кислотность (pH мочи)", "urine_specific_gravity": "Удельный вес (мочи)", 
    "urine_leukocytes": "Лейкоциты (в моче)", "urine_protein": "Белок (в моче)", 
    "urine_blood": "Кровь/Гемоглобин (в моче)", "urine_nitrites": "Нитриты (в моче)", 
    "urine_ketones": "Кетоны (в моче)", "urine_urobilinogen": "Уробилиноген (в моче)", 
    "urine_bilirubin": "Билирубин (в моче)", "urine_epithelium_flat": "Эпителий плоский (в моче)",
    "urine_epithelium_transitional": "Эпителий переходный (в моче)",
    "urine_epithelium_renal": "Эпителий почечный (в моче)",
    "urine_rbc_unchanged": "Эритроциты неизмененные (в моче)",
    "urine_rbc_changed": "Эритроциты измененные (в моче)", "urine_mucus": "Слизь (в моче)", 
    "urine_bacteria": "Бактерии (в моче)", "urine_crystals": "Кристаллы/Соли (в моче)", 
    "urine_cylinders": "Цилиндры (в моче)", "urine_yeast": "Дрожжеподобные грибы (в моче)",
    "reticulocytes": "Ретикулоциты", "metamyelocytes":"Метамиелоциты", "myelocytes": "Миелоциты"
}

@router.callback_query(AnalysisStates.waiting_input_method, F.data == "input_method_pdf")
async def process_input_method_pdf(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.message:
        try:
            await callback.message.delete()
        except TelegramBadRequest:
            pass
    await callback.message.answer("Пожалуйста, прикрепите PDF-файл с вашими анализами.")
    await state.set_state(AnalysisStates.waiting_for_pdf)

@router.callback_query(AnalysisStates.waiting_input_method, F.data == "cancel_analysis_input")
async def cancel_input_method_selection(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Отменено.")
    if callback.message:
        try:
            await callback.message.edit_text("Выбор метода ввода данных отменен.", reply_markup=None)
        except TelegramBadRequest:
            await safe_delete_message(callback.message.chat.id, callback.message.message_id)
            await callback.message.answer("Выбор метода ввода данных отменен.")
    await state.clear()


async def process_and_display_parsed_data(message_or_callback: types.Message | types.CallbackQuery, 
                                          state: FSMContext, 
                                          parsed_data: dict, 
                                          source: str):
    target_chat_id = message_or_callback.from_user.id
    source_display_name = "неизвестного источника"
    if source == "pdf": source_display_name = "PDF файла"
    elif source == "form_webapp": source_display_name = "онлайн формы"
    elif source.startswith("edited_from_"):
        original_source_name = source.split("edited_from_")[-1]
        if original_source_name == "pdf": source_display_name = "PDF файла (отредактировано)"
        elif original_source_name == "form_webapp": source_display_name = "онлайн формы (отредактировано)"
        else: source_display_name = "данных (отредактировано)"
    
    editable_text_lines = [f"✅ Обработанные данные анализов из {source_display_name}:\n"]
    text_output_parts = [f"✅ Обработанные данные анализов из {source_display_name}:\n"]
            
    found_any_data = False
    for key, value in parsed_data.items():
        display_name = DISPLAY_NAMES_MAP_ANALYSIS.get(key, key.replace("_", " ").capitalize())
        if key in DISPLAY_NAMES_MAP_ANALYSIS:
            text_output_parts.append(f"<b>{display_name}</b>: {value}")
            editable_text_lines.append(f"{key}: {value}")
            found_any_data = True
    
    if not found_any_data:
         await bot.send_message(target_chat_id,
             "К сожалению, не удалось найти известные показатели в предоставленных данных. "
             "Пожалуйста, проверьте корректность и попробуйте снова."
         )
         await state.set_state(AnalysisStates.waiting_input_method)
         await bot.send_message(target_chat_id, "Как вы хотите предоставить данные?", reply_markup=data_input_method_inline_keyboard())
         return

    full_text_output_html = "\n".join(text_output_parts)
    full_editable_text = "\n".join(editable_text_lines)
    
    await state.update_data(
        parsed_analysis_data=parsed_data, 
        editable_analysis_text=full_editable_text,
        analysis_source=source 
    ) 
    
    max_len = 4000 
    display_text_output_html = full_text_output_html[:max_len] + ("..." if len(full_text_output_html) > max_len else "")
    
    sent_message = await bot.send_message(target_chat_id, display_text_output_html, 
                         reply_markup=confirm_analysis_data_keyboard(),
                         parse_mode="HTML")
    await state.update_data(confirmation_message_id=sent_message.message_id)
    await state.set_state(AnalysisStates.waiting_for_confirmation)


@router.message(AnalysisStates.waiting_for_pdf, F.document)
async def handle_analysis_pdf(message: types.Message, state: FSMContext):
    document = message.document
    if document.mime_type != "application/pdf":
        await message.answer("Пожалуйста, прикрепите файл в формате PDF.")
        return
    MAX_FILE_SIZE_MB = 10
    if document.file_size > MAX_FILE_SIZE_MB * 1024 * 1024:
        await message.answer(f"Файл слишком большой. Пожалуйста, прикрепите PDF размером до {MAX_FILE_SIZE_MB} МБ.")
        return
    processing_msg = await message.answer(
        "Ваш PDF-файл получен. Начинаю обработку, это может занять некоторое время..."
    )
    try:
        file_info = await bot.get_file(document.file_id)
        downloaded_file_bytes_io = await bot.download_file(file_info.file_path)
        if not downloaded_file_bytes_io:
            await processing_msg.edit_text("Не удалось скачать файл. Попробуйте еще раз.")
            return
        pdf_bytes = downloaded_file_bytes_io.read()
        extracted_text = await extract_text_from_pdf_bytes_async(pdf_bytes) 
        if extracted_text:
            print("-" * 20 + " ИЗВЛЕЧЕННЫЙ ТЕКСТ ИЗ PDF (ПЕРЕД LLM ПАРСИНГОМ) " + "-" * 20)
            print(extracted_text[:2000] + ("..." if len(extracted_text) > 2000 else "")) 
            print("-" * 70)
        if not (extracted_text and extracted_text.strip() and \
                not extracted_text.startswith("Ошибка") and \
                not extracted_text.startswith("Не удалось извлечь текст")):
            error_message_text = extracted_text if extracted_text else \
                                 "Не удалось извлечь текст из PDF. Убедитесь, что это текстовый PDF, " \
                                 "а не скан-изображение без текстового слоя."
            await processing_msg.edit_text(error_message_text) 
            await message.answer("Вы можете попробовать еще раз, прикрепив другой PDF, или отменить действие командой /cancel.")
            return
        await processing_msg.edit_text(
            "Текст из файла успешно извлечен. Анализирую данные, пожалуйста, подождите..."
        )
        parsed_data_from_pdf = await llm_parse_medical_text_to_json(extracted_text)
        try:
            await processing_msg.delete() 
        except TelegramBadRequest:
            pass
        if parsed_data_from_pdf:
            await process_and_display_parsed_data(message, state, parsed_data_from_pdf, "pdf")
        else:
            await message.answer(
                "Не удалось обработать данные из вашего PDF файла. Возможно, формат документа не поддерживается "
                "или произошла ошибка при анализе. Попробуйте другой файл или проверьте его содержимое."
            )
            await state.set_state(AnalysisStates.waiting_input_method)
            await message.answer(
                "Пожалуйста, выберите метод ввода данных.",
                reply_markup=data_input_method_inline_keyboard()
            )
    except Exception as e:
        print(f"Критическая ошибка при обработке PDF: {e}")
        if 'processing_msg' in locals() and processing_msg:
             try: await processing_msg.delete()
             except TelegramBadRequest: pass
        await message.answer(
            f"Произошла неожиданная ошибка при обработке вашего PDF. "
            f"Пожалуйста, попробуйте позже или обратитесь к администратору."
        )
        await state.clear()


@router.message(F.web_app_data)
async def handle_web_app_data(message: types.Message, state: FSMContext):
    current_fsm_state = await state.get_state()
    print(f"DEBUG: WebApp data received. Current state: {current_fsm_state}")
    
    if not current_fsm_state or not (
        current_fsm_state == AnalysisStates.waiting_input_method.state or
        current_fsm_state.startswith("AnalysisStates:") 
        ):
        print(f"Получены данные WebApp в неожиданном состоянии: {current_fsm_state}. Игнорируется.")
        return

    if message.web_app_data:
        data_str = message.web_app_data.data
        processing_message = await message.answer("Данные из формы получены, обрабатываю...")
        try:
            parsed_data_from_form = json.loads(data_str)
            if isinstance(parsed_data_from_form, dict):
                await safe_delete_message(processing_message.chat.id, processing_message.message_id)
                await process_and_display_parsed_data(message, state, parsed_data_from_form, "form_webapp")
            else:
                await processing_message.edit_text("Получены некорректные данные из формы (не словарь). Попробуйте снова.")
                await state.set_state(AnalysisStates.waiting_input_method)
                await message.answer("Как вы хотите предоставить данные?", reply_markup=data_input_method_inline_keyboard())
        except json.JSONDecodeError:
            await processing_message.edit_text("Ошибка обработки данных из формы (неверный JSON). Попробуйте снова.")
            await state.set_state(AnalysisStates.waiting_input_method)
            await message.answer("Как вы хотите предоставить данные?", reply_markup=data_input_method_inline_keyboard())
        except Exception as e:
            print(f"Ошибка обработки данных из WebApp: {e}")
            await processing_message.edit_text("Произошла ошибка при обработке данных из формы.")
            await state.clear()


@router.callback_query(AnalysisStates.waiting_for_confirmation, F.data == "confirm_data_correct")
async def handle_data_confirmation_correct(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Данные подтверждены! Готовлю заключение...", show_alert=False)
    user_fsm_data = await state.get_data()
    parsed_analysis_data = user_fsm_data.get("parsed_analysis_data")
    confirmation_message_id = user_fsm_data.get("confirmation_message_id")

    if confirmation_message_id and callback.message and callback.message.message_id == confirmation_message_id:
        try:
            await callback.message.delete() 
        except TelegramBadRequest:
            pass
    elif callback.message:
         await safe_delete_message(callback.message.chat.id, callback.message.message_id)

    if not parsed_analysis_data:
        await bot.send_message(callback.from_user.id,
            "Произошла ошибка: не найдены данные для формирования заключения. "
            "Пожалуйста, попробуйте загрузить данные заново."
        )
        await state.set_state(AnalysisStates.waiting_input_method)
        await bot.send_message(callback.from_user.id, "Как вы хотите предоставить данные?", reply_markup=data_input_method_inline_keyboard())
        return

    save_success = await asyncio.to_thread(
        save_parsed_analysis_to_json, 
        callback.from_user.id, 
        parsed_analysis_data 
    )
    if not save_success:
        print(f"Ошибка сохранения данных анализа для user_id {callback.from_user.id}.")
        await bot.send_message(callback.from_user.id, "Внимание: произошла ошибка при сохранении ваших данных анализа, но я все равно попробую подготовить заключение.")

    user_profile = load_user_data_from_json(callback.from_user.id)
    if not user_profile or "registration_data" not in user_profile:
        await bot.send_message(callback.from_user.id,
            "Не удалось загрузить ваш профиль для подготовки заключения. "
            "Пожалуйста, попробуйте пройти регистрацию заново (/start)."
        )
        await state.clear()
        return
    
    reg_data = user_profile.get("registration_data", {})
    user_data_text_parts = ["1. Вводные данные пациента:"]
    gender_map = {"male": "Мужской", "female": "Женский"}
    user_data_text_parts.append(f"Пол: {gender_map.get(reg_data.get('gender'), 'Не указан')}")
    if reg_data.get('age'): user_data_text_parts.append(f"Возраст: {reg_data.get('age')} лет")
    if reg_data.get('weight'): user_data_text_parts.append(f"Вес: {reg_data.get('weight')} кг")
    if reg_data.get('height'): user_data_text_parts.append(f"Рост: {reg_data.get('height')} см")
    user_data_text_parts.append(f"Основные жалобы: {reg_data.get('complaints', 'Не указаны в профиле')}")

    med_history_list = reg_data.get('medical_history_list', [])
    med_history_text_input = reg_data.get('medical_history_text', '')
    chronic_diseases = "Не указаны"
    combined_history = []
    if med_history_list and "none" not in med_history_list :
        combined_history.extend(med_history_list)
    if med_history_text_input and med_history_text_input.lower() not in ["нет", "no", "", "none"]:
        combined_history.append(med_history_text_input)
    if combined_history: chronic_diseases = "; ".join(combined_history)
    elif "none" in med_history_list: chronic_diseases = "Отсутствуют (со слов пациента)"
    user_data_text_parts.append(f"Хронические заболевания: {chronic_diseases}")
    
    habits_list = reg_data.get('habits_list', [])
    habits_text_input = reg_data.get('habits_text', '')
    user_habits = "Не указаны"
    combined_habits = []
    if habits_list and "none" not in habits_list:
        combined_habits.extend(habits_list)
    if habits_text_input and habits_text_input.lower() not in ["нет", "no", "", "none"]:
        combined_habits.append(habits_text_input)
    if combined_habits: user_habits = "; ".join(combined_habits)
    elif "none" in habits_list: user_habits = "Отсутствуют (со слов пациента)"
    user_data_text_parts.append(f"Привычки: {user_habits}")
    user_data_final_text = "\n".join(user_data_text_parts)

    analysis_data_text_parts = ["2. Показатели анализа крови:"]
    for key, value in parsed_analysis_data.items():
        display_name = DISPLAY_NAMES_MAP_ANALYSIS.get(key, key) 
        analysis_data_text_parts.append(f"{display_name} {value}")
    analysis_data_final_text = "\n".join(analysis_data_text_parts)

    system_prompt_hematologist = "Вы — врач-гематолог. Дайте понятную, но профессиональную оценку анализа крови, которая будет полезна как пациенту, так и медицинским специалистам. Если пользователь укажет данные, которые не могут быть реальными или вызывают сомнение, проигнорируй их и добавь в конце ответа: “Некоторые данные вызывают сомнения и были проигнорированы!”"
    user_prompt_structure = f"""{user_data_final_text}

{analysis_data_final_text}

---
Формат ответа:

1. Оценка результатов
- Какие показатели отклоняются от нормы

2. О чем говорят изменения
- Возможные причины отклонений 
- Какие заболевания можно предположить
- Влияние возраста, пола и других факторов пациента

3. Что делать дальше
- Какие анализы/обследования нужны дополнительно
- Когда нужно срочно обратиться к врачу
- Какие изменения в образе жизни могут помочь

---

Требования к ответу:
Профессионально, но понятно для пациента  
Конкретно и по делу  
С указанием степени срочности рекомендаций  
Без излишней тревожности, но с указанием на опасные симптомы  

Избегать:
Чрезмерно сложных медицинских терминов без пояснений  
Расплывчатых формулировок  
Необоснованных предположений  

Ответ должен помочь пациенту понять свое состояние и дальнейшие действия, оставаясь при этом профессионально точным.
"""
    messages_for_llm = [
        {"role": "system", "content": system_prompt_hematologist},
        {"role": "user", "content": user_prompt_structure}
    ]

    await bot.send_message(callback.from_user.id, "Анализирую ваши данные и готовлю заключение... Это может занять до 2-3 минут.")
    
    llm_response = await get_llm_completion(messages=messages_for_llm, temperature=0.6, timeout=180) 

    final_keyboard = after_llm_result_keyboard()

    if llm_response:
        cleaned_llm_response = re.sub(r"<think>.*?</think>\s*", "", llm_response, flags=re.DOTALL).strip()
        max_message_length = 4000
        
        if len(cleaned_llm_response) == 0:
             await bot.send_message(callback.from_user.id, "Нейросеть не предоставила содержательного ответа. Попробуйте позже.", reply_markup=final_keyboard)
        elif len(cleaned_llm_response) > max_message_length:
            parts = []
            current_part = ""
            for line in cleaned_llm_response.splitlines(keepends=True):
                if len(current_part) + len(line) > max_message_length:
                    parts.append(current_part)
                    current_part = line
                else:
                    current_part += line
            if current_part:
                parts.append(current_part)
            
            for i, part_text in enumerate(parts):
                reply_markup_for_part = final_keyboard if i == len(parts) - 1 else None
                await bot.send_message(callback.from_user.id, part_text, parse_mode="Markdown", reply_markup=reply_markup_for_part)
                if i < len(parts) - 1: 
                    await asyncio.sleep(0.5)
        else:
            await bot.send_message(callback.from_user.id, cleaned_llm_response, parse_mode="Markdown", reply_markup=final_keyboard)
    else:
        await bot.send_message(callback.from_user.id,
            "К сожалению, не удалось получить заключение от нейросети. Попробуйте запросить позже или обратитесь к администратору.",
            reply_markup=final_keyboard
        )
    await state.clear()


@router.callback_query(F.data == "analyze_new_data")
async def analyze_new_data_prompt(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.message: # Удаляем сообщение с кнопками "Проанализировать другие / Перерегистрация"
        await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    
    await bot.send_message(callback.from_user.id, 
                           "Как вы хотите предоставить новые данные анализов?",
                           reply_markup=data_input_method_inline_keyboard())
    await state.set_state(AnalysisStates.waiting_input_method)

@router.callback_query(F.data == "reregister_profile")
async def reregister_profile_from_analysis_results(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Начинаем процесс перерегистрации...")
    if callback.message: # Удаляем сообщение с кнопками
        await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    
    await perform_reregistration(callback, state) # Используем общую функцию


@router.callback_query(AnalysisStates.waiting_for_confirmation, F.data == "confirm_data_edit_manual")
async def handle_data_confirmation_edit_manual(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_fsm_data = await state.get_data()
    editable_text = user_fsm_data.get("editable_analysis_text")
    analysis_source = user_fsm_data.get("analysis_source", "данных") 
    confirmation_message_id = user_fsm_data.get("confirmation_message_id")

    if not editable_text:
        if confirmation_message_id and callback.message and callback.message.message_id == confirmation_message_id:
            await safe_delete_message(callback.message.chat.id, callback.message.message_id)
        elif callback.message:
            await safe_delete_message(callback.message.chat.id, callback.message.message_id)
        await bot.send_message(callback.from_user.id,
            "Не найдены данные для редактирования. Пожалуйста, загрузите данные заново.",
        )
        await state.set_state(AnalysisStates.waiting_input_method)
        await bot.send_message(callback.from_user.id, "Как вы хотите предоставить данные?", reply_markup=data_input_method_inline_keyboard())
        return

    if confirmation_message_id and callback.message and callback.message.message_id == confirmation_message_id:
        await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    elif callback.message:
        await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    
    source_display_name = "данных"
    if analysis_source == "pdf": source_display_name = "PDF файла"
    elif analysis_source == "form_webapp": source_display_name = "онлайн формы"
    elif analysis_source.startswith("edited_from_"):
        original_source_name = analysis_source.split("edited_from_")[-1]
        if original_source_name == "pdf": source_display_name = "PDF файла (отредактировано ранее)"
        elif original_source_name == "form_webapp": source_display_name = "онлайн формы (отредактировано ранее)"
        else: source_display_name = "данных (отредактировано ранее)"

    instruction_message_text = (
        f"Вы собираетесь редактировать данные, полученные из {source_display_name}.\n"
        "Нажмите кнопку 'Показать текст для копирования', чтобы увидеть данные в удобном для копирования виде. "
        "Затем скопируйте его, отредактируйте и отправьте мне как обычное сообщение.\n\n"
        "**Формат для редактирования:**\n"
        "`ключ_показателя: новое значение`\n"
        "Каждый показатель на новой строке. Убедитесь, что ключи (на английском) не изменены.\n"
        "Если хотите удалить показатель, сотрите всю строку с ним или оставьте значение пустым."
    )
    await bot.send_message(callback.from_user.id, instruction_message_text, 
                           reply_markup=after_edit_prompt_keyboard(),
                           parse_mode="Markdown")
    await state.set_state(AnalysisStates.waiting_for_edited_text)


@router.callback_query(AnalysisStates.waiting_for_edited_text, F.data == "resend_editable_text")
async def resend_editable_text_for_copy(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Текст для копирования ниже.")
    user_fsm_data = await state.get_data()
    editable_text = user_fsm_data.get("editable_analysis_text")

    if callback.message:
        await safe_delete_message(callback.message.chat.id, callback.message.message_id)

    if editable_text:
        text_for_copy = (
            "--- ТЕКСТ ДЛЯ КОПИРОВАНИЯ И РЕДАКТИРОВАНИЯ ---\n"
            "```text\n"
            f"{editable_text}\n"
            "```\n"
            "После редактирования, просто отправьте исправленный текст."
        )
        await bot.send_message(callback.from_user.id, text_for_copy, parse_mode="Markdown")
    else:
        await bot.send_message(callback.from_user.id, "Не удалось найти текст для редактирования. Пожалуйста, начните сначала.")
        await state.clear()
        await bot.send_message(callback.from_user.id, "Как вы хотите предоставить данные?", reply_markup=data_input_method_inline_keyboard())
        await state.set_state(AnalysisStates.waiting_input_method)

@router.callback_query(AnalysisStates.waiting_for_edited_text, F.data == "cancel_edit_and_return")
async def cancel_edit_and_return_to_method_selection(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer("Редактирование отменено.")
    if callback.message:
        await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    
    await bot.send_message(callback.from_user.id, "Редактирование отменено. Как вы хотите предоставить данные анализов?", 
                           reply_markup=data_input_method_inline_keyboard())
    await state.set_state(AnalysisStates.waiting_input_method)


@router.callback_query(AnalysisStates.waiting_for_confirmation, F.data == "force_reload_data_source")
async def handle_force_reload_data_source(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    user_fsm_data = await state.get_data()
    confirmation_message_id = user_fsm_data.get("confirmation_message_id")
    if confirmation_message_id and callback.message and callback.message.message_id == confirmation_message_id:
        await safe_delete_message(callback.message.chat.id, callback.message.message_id)
    elif callback.message:
         await safe_delete_message(callback.message.chat.id, callback.message.message_id)

    await bot.send_message(callback.from_user.id, "Как вы хотите предоставить данные анализов?", reply_markup=data_input_method_inline_keyboard())
    await state.set_state(AnalysisStates.waiting_input_method)


@router.message(AnalysisStates.waiting_for_edited_text, F.text)
async def handle_edited_analysis_text(message: types.Message, state: FSMContext):
    edited_text = message.text
    parsed_edited_data = {}
    possible_error = False
    try:
        lines = edited_text.splitlines()
        user_fsm_data = await state.get_data()
        analysis_source = user_fsm_data.get("analysis_source", "данных") 
        
        potential_headers = [
            "✅ Обработанные данные анализов из PDF файла:",
            "✅ Обработанные данные анализов из онлайн формы:",
            "✅ Обработанные данные анализов из PDF файла (отредактировано):",
            "✅ Обработанные данные анализов из онлайн формы (отредактировано):",
            "✅ Обработанные данные анализов (для редактирования скопируйте этот текст):",
            "--- ТЕКСТ ДЛЯ КОПИРОВАНИЯ И РЕДАКТИРОВАНИЯ ---" 
        ]
        potential_headers = [h.strip() for h in potential_headers]

        cleaned_lines = []
        header_skipped = False
        for line in lines:
            stripped_line = line.strip()
            if not header_skipped and stripped_line in potential_headers:
                header_skipped = True
                continue
            if stripped_line == "```text" or stripped_line == "```":
                continue
            cleaned_lines.append(line)
        
        for line_to_parse in cleaned_lines:
            line_to_parse = line_to_parse.strip()
            if not line_to_parse: continue
            if ':' not in line_to_parse:
                if line_to_parse.strip(): print(f"Skipping line due to missing colon: '{line_to_parse}'")
                continue
            key, value = line_to_parse.split(':', 1)
            key = key.strip()
            value = value.strip()
            if key:
                parsed_edited_data[key] = value
            else:
                print(f"Skipping line due to empty key: '{line_to_parse}'")
    except Exception as e:
        print(f"Error parsing edited text: {e}")
        possible_error = True

    if not parsed_edited_data and not possible_error:
        await message.answer(
            "Не удалось распознать формат отредактированных данных или вы отправили пустой список.\n"
            "Убедитесь, что каждая строка имеет вид `ключ: значение`. "
            "Пожалуйста, попробуйте снова, или отмените (/cancel), или загрузите данные заново."
        )
        return
    elif possible_error:
         await message.answer(
            "Произошла ошибка при обработке ваших правок. "
            "Пожалуйста, проверьте формат, попробуйте снова, или отмените (/cancel), или загрузите данные заново."
        )
         return
    original_source = analysis_source.split("edited_from_")[-1] if "edited_from_" in analysis_source else analysis_source
    await process_and_display_parsed_data(message, state, parsed_edited_data, f"edited_from_{original_source}")


@router.message(AnalysisStates.waiting_input_method, F.text)
async def handle_wrong_text_for_method_selection(message: types.Message, state: FSMContext):
    await message.answer(
        "Пожалуйста, выберите метод предоставления данных с помощью кнопок выше или отмените действие (/cancel)."
    )

@router.message(AnalysisStates.waiting_for_pdf, F.text) 
async def handle_wrong_text_for_pdf(message: types.Message, state: FSMContext):
    await message.answer(
        "Пожалуйста, прикрепите PDF-файл с вашими анализами или отмените действие командой /cancel."
    )

@router.message(AnalysisStates.waiting_for_confirmation, F.text) 
async def handle_wrong_text_for_confirmation(message: types.Message, state: FSMContext):
    await message.answer(
        "Пожалуйста, используйте кнопки '✅ Все верно', '✏️ Редактировать' или '🔄 Ввести другие данные', "
        "или отмените действие командой /cancel."
    )

@router.message(AnalysisStates.waiting_for_edited_text, ~F.text)
async def handle_wrong_media_for_edited_text(message: types.Message, state: FSMContext):
    await message.answer(
        "Я ожидаю от вас отредактированный текст анализов. Пожалуйста, отправьте текст или отмените (/cancel)."
    )

@router.message(AnalysisStates.waiting_input_method, F.document)
async def handle_doc_in_method_selection(message: types.Message, state: FSMContext):
    if message.document and message.document.mime_type == "application/pdf":
        await state.set_state(AnalysisStates.waiting_for_pdf)
        await handle_analysis_pdf(message, state)
    else:
        await message.answer(
            "Пожалуйста, выберите метод предоставления данных с помощью кнопок или загрузите PDF-файл."
        )
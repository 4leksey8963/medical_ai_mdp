# utils/llm_service.py
import asyncio
import json
import requests
import re 
from typing import Optional, List, Dict

try:
    from ai_conf.get_models import getter_models_ai
except ImportError:
    try:
        from ai_conf.get_models import getter_models_ai 
    except ImportError:
        from ai_conf.get_models import getter_models_ai
try:
    from ..config import api_token
except ImportError:
    from config import api_token

LLM_API_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"

async def get_llm_completion(
    messages: List[Dict[str, str]],
    model_id: Optional[str] = None,
    temperature: float = 0.1, 
    timeout: int = 60 
) -> Optional[str]:
    global api_token 
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + api_token
    }
    final_model_id = model_id
    if not final_model_id:
        try:
            available_models = getter_models_ai()
            if not available_models:
                print("LLM Service: Не удалось получить список доступных моделей AI.")
                return None
            final_model_id = available_models[0]
        except Exception as e:
            print(f"LLM Service: Ошибка при получении моделей AI: {e}")
            return None
    if not final_model_id: 
        print("LLM Service: ID модели не указан и не удалось получить его автоматически.")
        return None
    data_payload = {
        "model": final_model_id,
        "messages": messages,
        "temperature": temperature
    }
    try:
        def sync_llm_request():
            response = requests.post(LLM_API_URL, headers=headers, json=data_payload, timeout=timeout)
            response.raise_for_status()
            response_data = response.json()
            if 'choices' in response_data and response_data['choices'] and \
               'message' in response_data['choices'][0] and \
               'content' in response_data['choices'][0]['message']:
                return response_data['choices'][0]['message']['content']
            else:
                print(f"LLM Service Error: 'choices', 'message' or 'content' not found. Data: {response_data}")
                return None
        response_text = await asyncio.to_thread(sync_llm_request)
        return response_text
    except requests.exceptions.Timeout:
        print(f"LLM Service: API request timed out after {timeout} seconds.")
        return None
    except requests.exceptions.RequestException as e:
        print(f"LLM Service: API Request failed: {e}")
        return None
    except Exception as e:
        print(f"LLM Service: An unexpected error occurred: {e}")
        return None

async def llm_parse_medical_text_to_json(text_from_pdf: str) -> Optional[dict]:
    system_prompt = """Ты — эксперт по анализу медицинских документов. Твоя задача - извлечь ключевые показатели из предоставленного текста медицинского анализа (например, общего анализа крови, биохимии, общего анализа мочи) и вернуть их в строго определенном JSON формате. Внимательно читай названия показателей, включая аббревиатуры в скобках, и их единицы измерения. Если показатель представлен и в абсолютных значениях, и в процентах, извлеки оба с разными ключами, если это указано в списке."""
    desired_analyses = {
        "hemoglobin": "Гемоглобин (Hb)", "rbc": "Эритроциты (RBC)", "hematocrit": "Гематокрит (HCT)", 
        "mcv": "Средний объем эритроцита (MCV)", "mch": "Среднее содержание Hb в эритроците (MCH)", 
        "mchc": "Средняя концентрация Hb в эритроците (MCHC)", "rdw_cv": "Гетерогенность эритроцитов (RDW или RDW-CV)",
        "rdw_sd": "Гетерогенность эритроцитов (RDW или RDW-SD)", "nrbc_abs": "Нормобласты (NRBC) абсолютное значение",
        "nrbc_pct": "Нормобласты (NRBC) процент", "macrocytes_pct": "Макроциты (MacroR)",
        "microcytes_pct": "Микроциты (MicroR)", "color_index": "Цветовой показатель",
        "plt": "Тромбоциты (PLT)", "pct": "Тромбокрит (PCT)", "mpv": "Средний объем тромбоцитов (MPV)",
        "pdw": "Гетерогенность тромбоцитов по объему (PDW)", "p_lcr": "Коэффициент числа крупных тромбоцитов (P-LCR)",
        "wbc": "Лейкоциты (WBC)", "neutrophils_abs": "Нейтрофилы (NEU) абсолютное значение",
        "neutrophils_pct": "Нейтрофилы (NEU) процент", "band_neutrophils_abs": "Палочкоядерные нейтрофилы абсолютное значение",
        "band_neutrophils_pct": "Палочкоядерные нейтрофилы процент", "seg_neutrophils_abs": "Сегментоядерные нейтрофилы абсолютное значение",
        "seg_neutrophils_pct": "Сегментоядерные нейтрофилы процент", "eosinophils_abs": "Эозинофилы (EOS) абсолютное значение",
        "eosinophils_pct": "Эозинофилы (EOS) процент", "basophils_abs": "Базофилы (BAS) абсолютное значение",
        "basophils_pct": "Базофилы (BAS) процент", "monocytes_abs": "Моноциты (MON) абсолютное значение",
        "monocytes_pct": "Моноциты (MON) процент", "lymphocytes_abs": "Лимфоциты (LYM) абсолютное значение",
        "lymphocytes_pct": "Лимфоциты (LYM) процент", "ig_abs": "Незрелые гранулоциты (IG) абсолютное значение",
        "ig_pct": "Незрелые гранулоциты (IG) процент", "re_lymp_abs": "Реактивные лимфоциты (RE-LYMP) абсолютное значение",
        "re_lymp_pct": "Реактивные лимфоциты (RE-LYMP) процент", "as_lymp_abs": "Плазматические клетки (AS-LYMP) абсолютное значение",
        "as_lymp_pct": "Плазматические клетки (AS-LYMP) процент", "neut_ri": "Интенсивность реактивности нейтрофилов (NEUT-RI)",
        "neut_gi": "Показатель гранулярности нейтрофилов (NEUT-GI)", "esr": "СОЭ (по Вестергрену или просто СОЭ)",
        "protein_total": "Общий белок", "albumin": "Альбумин", "glucose": "Глюкоза",
        "cholesterol_total": "Холестерин общий", "hdl": "ЛПВП (HDL)", "ldl": "ЛПНП (LDL)",
        "triglycerides": "Триглицериды", "bilirubin_total": "Билирубин общий",
        "bilirubin_direct": "Билирубин прямой", "bilirubin_indirect": "Билирубин непрямой",
        "alt": "АЛТ (ALT)", "ast": "АСТ (AST)", "creatinine": "Креатинин",
        "urea": "Мочевина", "potassium": "Калий (K)", "sodium": "Натрий (Na)", "chloride": "Хлор (Cl)",
        "urine_color": "Цвет (мочи)", "urine_clarity": "Прозрачность (мочи)", 
        "urine_ph": "Кислотность (pH мочи)", "urine_specific_gravity": "Удельный вес (мочи)", 
        "urine_leukocytes": "Лейкоциты (в моче/лейкоцитарная эстераза)", "urine_protein": "Белок (в моче)", 
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
    instruction_lines = [
        "Проанализируй следующий текст, извлеченный из медицинского анализа. Это может быть общий анализ крови (ОАК), биохимический анализ крови (БАК), общий анализ мочи (ОАМ) или их комбинация.",
        "Извлеки следующие показатели (если они присутствуют) и их значения. Ключи в JSON должны быть на английском языке, как указано в списке ниже."
    ]
    for key, name in desired_analyses.items():
        instruction_lines.append(
            f"- {name} (ключ в JSON: \"{key}\", значение должно быть строкой, включающей число и единицы измерения, "
            f"если есть, например \"148,10 г/л\" или \"4,98 10^12/л\" или \"0,00 %\". "
            f"Если значение текстовое, например \"отрицательно\", то используй его.)"
        )
    instruction_lines.extend([
        "Если показатель имеет числовое значение и единицы измерения, включи их вместе в значение как одну строку. Например, \"148,10 г/л\" или \"4,98 10^12/л\".",
        "Если показатель текстовый (например, \"отрицательно\", \"следы\", \"не обнаружено\", \"желтый\"), используй это текстовое значение.",
        "Если показатель отсутствует в тексте, не включай его в JSON. Не придумывай значения.",
        "Не добавляй никакие другие поля, кроме указанных в списке выше.",
        "Не включай в JSON референсные значения, комментарии лаборатории, ФИО пациента, дату и т.п., только фактический результат анализа для каждого показателя из списка.",
        "Ответ должен быть ТОЛЬКО JSON объектом без каких-либо дополнительных пояснений, комментариев или markdown-разметки типа ```json ... ```.",
        "Пример желаемого JSON формата:",
        "{",
        "  \"hemoglobin\": \"148,10 г/л\",",
        "  \"rbc\": \"4,98 10^12/л\",",
        "  \"hematocrit\": \"41,60 %\",",
        "  \"neutrophils_abs\": \"4,00 10^9/л\",",
        "  \"neutrophils_pct\": \"65,90 %\",",
        "  \"urine_protein\": \"отрицательно\"",
        "  // ... и другие поля из списка, если они найдены",
        "}"
    ])
    user_prompt_instructions = "\n".join(instruction_lines)
    MAX_PDF_TEXT_LENGTH = 15000 
    if len(text_from_pdf) > MAX_PDF_TEXT_LENGTH:
        print(f"LLM Parser Warning: PDF text is too long ({len(text_from_pdf)} chars), truncating to {MAX_PDF_TEXT_LENGTH} chars.")
        text_from_pdf_for_llm = text_from_pdf[:MAX_PDF_TEXT_LENGTH] + "\n... (текст был усечен из-за большой длины)"
    else:
        text_from_pdf_for_llm = text_from_pdf
    full_user_prompt = f"{user_prompt_instructions}\n\nВот текст для анализа:\n--- НАЧАЛО ТЕКСТА ИЗ PDF ---\n{text_from_pdf_for_llm}\n--- КОНЕЦ ТЕКСТА ИЗ PDF ---"
    messages_payload = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": full_user_prompt}
    ]
    response_text_from_llm = await get_llm_completion(messages=messages_payload, temperature=0.05, timeout=120) 
    if not response_text_from_llm:
        return None
    cleaned_response = response_text_from_llm.strip()
    json_match = re.search(r"\{[\s\S]*\}", cleaned_response)
    if json_match:
        cleaned_response = json_match.group(0)
    else:
        if cleaned_response.startswith("```json"):
            cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
        elif cleaned_response.startswith("```"):
            cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
        cleaned_response = cleaned_response.strip()
    try:
        parsed_json = json.loads(cleaned_response)
        if not isinstance(parsed_json, dict):
            print(f"LLM Parser: Ответ не JSON-объект. Получено: {type(parsed_json)}")
            print(f"Raw LLM response for debug: {response_text_from_llm}")
            return None
        return parsed_json
    except json.JSONDecodeError as e:
        print(f"LLM Parser: Failed to decode JSON from LLM response: {e}")
        print(f"Raw LLM response for debug: {response_text_from_llm}")
        print(f"Cleaned response attempt: {cleaned_response}")
        return None
    except Exception as e:
        print(f"LLM Parser: Unexpected error processing LLM JSON response: {e}")
        return None
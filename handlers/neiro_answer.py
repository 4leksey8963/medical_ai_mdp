from aiogram import Router, types
import asyncio
import re 
# Используем новую общую функцию
from utils.llm_service import get_llm_completion # Новый импорт

router = Router()

@router.message() # Этот хэндлер должен идти ПОСЛЕ всех остальных специфичных хэндлеров
async def handle_unknown_messages_with_llm(message: types.Message):
    # Проверяем, не является ли это командой или чем-то, что должно быть обработано ранее
    if message.text and message.text.startswith('/'):
        return 

    typing_msg = await message.answer("Думаю...") 

    system_prompt = "Ты врач терапевт, дружелюбный и готовый помочь с вопросами о здоровье. Отвечай кратко и по делу."
    
    user_message_text = message.text
    
    messages_payload = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message_text}
    ]

    raw_api_response_text = await get_llm_completion(messages=messages_payload, temperature=0.7, timeout=45)

    await message.bot.delete_message(chat_id=message.chat.id, message_id=typing_msg.message_id)

    if raw_api_response_text and raw_api_response_text.strip():
        # Удаляем <think>...</think> если они есть (ваша логика)
        clean_content = re.sub(r"<think>.*?</think>\s*", "", raw_api_response_text, flags=re.DOTALL).strip()
        
        if not clean_content and raw_api_response_text:
             print(f"Warning: Entire response was within <think> tags for general question. Raw: {raw_api_response_text}")
             # Если все было в <think>, возможно, модель не хотела отвечать.
             await message.answer("Извините, я не могу ответить на этот вопрос так, чтобы это было полезно.")
        elif clean_content:
            await message.answer(clean_content, parse_mode='Markdown') # Используйте Markdown, если модель его поддерживает
        else:
            await message.answer("Извините, я не смог сформулировать ответ. Попробуйте переформулировать ваш вопрос.")
    else:
        await message.answer("Сервис временно недоступен или не смог обработать ваш запрос. Пожалуйста, попробуйте позже.")
from aiogram import Router, types
import requests
from ai_conf.get_models import getter_models_ai
from config import api_token

router = Router()

# Словарь для хранения последних сообщений бота по chat_id
last_bot_messages = {}

@router.message()
async def handle_unknown_messages(message: types.Message):
    # Отправляем временное сообщение
    typing_msg = await message.answer("Печатает...")
    
    # Ваш запрос к API
    url = "https://api.intelligence.io.solutions/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer "+api_token
    }
    
    data = {
        "model": getter_models_ai()[0],
        "messages": [
            {"role": "system", "content": "Ты врач терапевт"},
            {"role": "user", "content": message.text}
        ]
    }
    
    response = requests.post(url, headers=headers, json=data)
    response_data = response.json()
    text_message = response_data['choices'][0]['message']['content']
    
    # Удаляем сообщение "Печатает..."
    await message.bot.delete_message(
        chat_id=message.chat.id,
        message_id=typing_msg.message_id
    )
    
    
    # Отправляем новый ответ
    await message.answer(text_message, parse_mode='Markdown')
    
 
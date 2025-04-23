import requests
from get_models import getter_models_ai
from pprint import pprint
from config import api_token

url = "https://api.intelligence.io.solutions/api/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer "+api_token
}

data = {
    "model": "" + getter_models_ai()[0],
    "messages": [
        {
            "role": "system",
            "content": "Ты врач терапевт"
        },
        {
            "role": "user",
            "content": "Кто ты по профессии?"
        }
    ]
}

try:
    response = requests.post(url, headers=headers, json=data, timeout=5)
    response_data = response.json()

    # Проверяем статус и наличие 'choices'
    if response.status_code != 200:
        error_msg = response_data.get("error", "Unknown error")
        print(f"API Error (HTTP {response.status_code}): {error_msg}")

    if 'choices' not in response_data:
        print("Invalid API response (no 'choices'):", response_data)

    text_message = response_data['choices'][0]['message']['content']
    print(text_message)

except requests.exceptions.Timeout:
    print("Сервер не ответил за 5 секунд!")
except Exception as e:
    print(f"Unexpected error: {e}")

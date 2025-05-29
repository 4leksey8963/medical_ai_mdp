import requests
from config import api_token


def getter_models_ai():
    url = "https://api.intelligence.io.solutions/api/v1/models"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer " + api_token
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching models from API: {e}")
        return [] 
    except ValueError: 
        print("Error decoding JSON from models API response.")
        return []

    models = []
    if 'data' in data and isinstance(data['data'], list):
        for model_info in data['data']:
            if isinstance(model_info, dict) and 'id' in model_info:
                name = model_info['id']
                if "qwen" in name.lower():
                    models.append(name)
            else:
                print(f"Skipping malformed model_info entry: {model_info}")
    else:
        print(f"API response for models does not contain a valid 'data' list. Response: {data}")
        return [] 

    if not models:
        print("Warning: No models matching 'queen' or 'deepseek' were found.")
    print(models)
    return models
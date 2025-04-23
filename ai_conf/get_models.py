import requests
from pprint import pprint
from config import api_token


def getter_models_ai():
    url = "https://api.intelligence.io.solutions/api/v1/models"

    headers = {
        "accept": "application/json",
        "Authorization": "Bearer "+api_token
    }

    response = requests.get(url, headers=headers)
    data = response.json()
    # pprint(data)
    models = []
    for i in range(len(data['data'])):
        name = data['data'][i]['id']
        models.append(name)
    return models
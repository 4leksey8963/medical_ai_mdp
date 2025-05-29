import json
import os
from pathlib import Path
from aiogram.types import User

BASE_DIR = Path(__file__).resolve().parent.parent
PERSON_DATA_DIR = BASE_DIR / "person_data"

def save_user_data_to_json(user: User, data: dict) -> bool:
    user_id = user.id
    user_folder_path = PERSON_DATA_DIR / str(user_id)
    try:
        user_folder_path.mkdir(parents=True, exist_ok=True)
        file_path = user_folder_path / "profile.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Данные пользователя {user_id} успешно сохранены в {file_path}")
        return True
    except IOError as e:
        print(f"Ошибка при сохранении данных для пользователя {user_id}: {e}")
        return False
    except Exception as e:
        print(f"Непредвиденная ошибка при сохранении данных для пользователя {user_id}: {e}")
        return False

def load_user_data_from_json(user_id: int) -> dict | None:
    user_folder_path = PERSON_DATA_DIR / str(user_id)
    file_path = user_folder_path / "profile.json"
    if not file_path.exists():
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except (IOError, json.JSONDecodeError) as e:
        print(f"Ошибка при загрузке данных для пользователя {user_id}: {e}")
        return None
    except Exception as e:
        print(f"Непредвиденная ошибка при загрузке данных для пользователя {user_id}: {e}")
        return None
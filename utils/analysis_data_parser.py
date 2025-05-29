import json
from pathlib import Path
from typing import Dict # Убрали Optional, List, Tuple, если не используются
import datetime

BASE_DIR = Path(__file__).resolve().parent.parent # Путь может потребовать корректировки
PERSON_DATA_DIR = BASE_DIR / "person_data"


def save_parsed_analysis_to_json(user_id: int, analysis_data: Dict[str, str], filename_prefix: str = "parsed_analysis") -> bool:
    user_folder_path = PERSON_DATA_DIR / str(user_id)
    try:
        user_folder_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = user_folder_path / f"{filename_prefix}_{timestamp}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_data, f, ensure_ascii=False, indent=4)
        print(f"Данные анализов пользователя {user_id} сохранены в {file_path}")
        return True
    except IOError as e:
        print(f"Ошибка при сохранении данных анализов для пользователя {user_id}: {e}")
        return False
    except Exception as e:
        print(f"Непредвиденная ошибка при сохранении данных анализов для пользователя {user_id}: {e}")
        return False
from aiogram.fsm.state import State, StatesGroup

class RegistrationStates(StatesGroup):
    waiting_for_registration_start = State()
    waiting_for_gender = State()
    waiting_for_age = State()
    waiting_for_weight = State()
    waiting_for_height = State()
    waiting_for_medical_history = State()
    waiting_for_habits = State()
    waiting_for_diet_features = State()
    waiting_for_sleep_pattern = State()

class AnalysisStates(StatesGroup):
    waiting_input_method = State()    # <--- ЭТО СОСТОЯНИЕ КЛЮЧЕВОЕ
    waiting_for_pdf = State()
    waiting_for_confirmation = State() 
    waiting_for_edited_text = State()
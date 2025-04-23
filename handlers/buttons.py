from aiogram import Router, types

router = Router()

@router.message(lambda msg: msg.text in ["ℹ️ О боте", "🔍 Поиск", "⚙️ Настройки", "⚙️ Настройки"])
async def handle_buttons(message: types.Message):
    if message.text == "ℹ️ О боте":
        await message.answer("Это тестовый бот")
    elif message.text == "🔍 Поиск":
        await message.answer("Функция поиска")
    else:
        await message.answer("Раздел настроек")
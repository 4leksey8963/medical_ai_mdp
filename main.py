# main.py
from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Убедитесь, что импорты соответствуют вашей структуре
from config import bot # bot инициализируется в config.py
from handlers import commands as common_handlers 
from handlers import registration as registration_handlers
from handlers import buttons as buttons_handlers 
from handlers import neiro_answer as neiro_handlers 
from handlers import analysis_handler 

import asyncio
import logging

async def main():
    logging.basicConfig(level=logging.INFO)

    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Порядок роутеров важен
    dp.include_router(common_handlers.router)
    dp.include_router(registration_handlers.router)
    dp.include_router(analysis_handler.router) # Обработка анализов (PDF и WebApp)
    dp.include_router(buttons_handlers.router) 
    
    # Роутер для ответов LLM на произвольные сообщения должен быть одним из последних
    dp.include_router(neiro_handlers.router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
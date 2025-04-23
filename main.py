from aiogram import Dispatcher
from config import bot
from handlers import commands, buttons, neiro_answer
import asyncio

async def main():
    dp = Dispatcher()
    dp.include_routers(
        commands.router,
        buttons.router,
        neiro_answer.router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
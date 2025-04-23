from aiogram import Router, types
from aiogram.filters import Command
from keyboards.reply import main_keyboard

router = Router()


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 <b>Добро пожаловать!</b>\nВыберите действие:",
        reply_markup=main_keyboard()
    )

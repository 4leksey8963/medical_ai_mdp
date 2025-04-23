from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

BOT_TOKEN = "7501012493:AAHbh83RZbFcuT_GEqqtKivJI3jOMfr6tFg"

api_token = "io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6Ijg3NjJiNmQ3LTM4OTAtNDMyZi1hMDRkLWQ1MjZkMzljNTk2YSIsImV4cCI6NDg5OTAzNDIxM30.Pf61Sy4ADbzwIOlRwU_7Kdr963V4j8S14BUez6_0gnCmY2oia_44claputNthrp_NFT3vO3_PYNHR0FSl0wWOw"

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML))
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from handlers.admin import router as admin_router
from handlers.user import router as user_router
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

token = os.getenv("BOT_TOKEN")
admin_id = int(os.getenv("ADMIN_ID"))

async def main():
    # Logging faylga yoziladi
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler("bot.log"),
            logging.StreamHandler()
        ]
    )

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    # Routerlarni ro'yxatdan o'tkazishdan oldin filtr qo'shamiz
    async def filter_admin(message: types.Message):
        return message.from_user.id == admin_id

    async def filter_admin_cb(callback: types.CallbackQuery):
        return callback.from_user.id == admin_id

    admin_router.message.filter(filter_admin)
    admin_router.callback_query.filter(filter_admin_cb)

    dp.include_router(admin_router)
    dp.include_router(user_router)

    # Bot komandalarini sozlash
    await bot.set_my_commands([
        BotCommand(command="start", description="Botni boshlash")
    ])

    # Polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

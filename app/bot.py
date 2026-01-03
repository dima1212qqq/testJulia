import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from app.config import BOT_TOKEN
from app.broker import broker
from app.tasks import perform_search
from app.storage import storage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Bot and Dispatcher
dp = Dispatcher()
bot = Bot(token=BOT_TOKEN)

@dp.message(CommandStart())
async def command_start_handler(message: types.Message):
    await message.answer(
        "👋 Привет! Я агрегатор маркетплейсов (Ozon, WB).\n"
        "Напиши мне название товара, и я найду лучшие цены."
    )

@dp.message()
async def search_handler(message: types.Message):
    query = message.text
    if not query:
        return

    await message.answer(f"🔍 Ищу '{query}' на площадках... Это займет минуту.")

    # 1. Check Cache first (Vibe coding: Instant answer)
    try:
        cached_results = await storage.search_products(query, limit=5)
        if cached_results:
             # Sort by price
            cached_results.sort(key=lambda x: x['price'])

            text = f"⚡ **Найдено в кэше для '{query}':**\n\n"
            for p in cached_results:
                source_icon = "🔵" if p['source'] == "Ozon" else "🟣"
                text += f"{source_icon} [{p['title']}]({p['url']})\n"
                text += f"💰 **{p['price']:,.0f} ₽**\n\n"

            text += "🔄 Запускаю поиск свежих данных..."
            await message.answer(text, parse_mode="Markdown")
    except Exception as e:
        logger.warning(f"Cache check failed: {e}")

    # 2. Dispatch Task
    await perform_search.kiq(query, message.chat.id)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

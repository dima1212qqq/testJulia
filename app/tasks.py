import asyncio
import logging
from app.broker import broker
from app.storage import storage
from app.scrapers.ozon import OzonScraper
from app.scrapers.wb import WBScraper
from app.scrapers.ym import YMScraper
from app.config import BOT_TOKEN
from aiogram import Bot

logger = logging.getLogger(__name__)

@broker.task
async def perform_search(query: str, chat_id: int):
    """
    Task to perform search:
    1. Scrape Ozon, WB, YM
    2. Save to Storage
    3. Notify User
    """
    logger.info(f"Starting search for: {query}")

    # 1. Scrape in parallel
    scrapers = [
        OzonScraper(headless=True),
        WBScraper(headless=True),
        YMScraper(headless=True)
    ]

    tasks = [scraper.scrape(query) for scraper in scrapers]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    all_products = []
    for res in results_list:
        if isinstance(res, list):
            all_products.extend(res)
        else:
            logger.error(f"Scraper error: {res}")

    # 2. Save to Storage (Meilisearch)
    if all_products:
        try:
            # Ensure index exists
            await storage.init_index()
            # Add products
            await storage.add_products(all_products)
        except Exception as e:
            logger.error(f"Failed to save to storage: {e}")

    # 3. Format Message
    if not all_products:
        text = f"По запросу '{query}' ничего не найдено на площадках :("
    else:
        # Sort by price
        all_products.sort(key=lambda x: x['price'])

        text = f"🔎 **Результаты для '{query}':**\n\n"

        # Show top 5 cheapest
        for p in all_products[:5]:
            source_icon = "🔵" if p['source'] == "Ozon" else "🟣" if p['source'] == "WB" else "🟡"
            text += f"{source_icon} [{p['title']}]({p['url']})\n"
            text += f"💰 **{p['price']:,.0f} ₽**\n\n"

        text += f"Всего найдено: {len(all_products)} товаров."

    # 4. Send to Telegram
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        await bot.session.close()
    except Exception as e:
        logger.error(f"Failed to send telegram message: {e}")

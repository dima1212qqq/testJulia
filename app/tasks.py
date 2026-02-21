import asyncio
import logging
from app.broker import broker
from app.storage import storage
from app.scrapers.ozon import OzonScraper
from app.scrapers.wb import WBScraper
from app.config import BOT_TOKEN
from aiogram import Bot

logger = logging.getLogger(__name__)

@broker.task
async def perform_search(query: str, chat_id: int):
    """
    Task to perform search:
    1. Scrape Ozon, WB
    2. Save to Storage
    3. Notify User
    """
    logger.info(f"Starting search for: {query}")

    # 1. Scrape in parallel
    scrapers = [
        OzonScraper(headless=True),
        WBScraper(headless=True)
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
    # Filter out fallback items from storage? Or store them but handle differently?
    # Better to store only real products for caching purposes.
    real_products = [p for p in all_products if not p.get('is_fallback')]
    if real_products:
        try:
            await storage.init_index()
            await storage.add_products(real_products)
        except Exception as e:
            logger.error(f"Failed to save to storage: {e}")

    # 3. Format Message
    if not all_products:
        text = f"По запросу '{query}' ничего не найдено на площадках :("
    else:
        # Sort: Real products first (by price), then fallback items
        def sort_key(p):
            is_fallback = p.get('is_fallback', False)
            price = p['price'] if p['price'] > 0 else float('inf')
            return (is_fallback, price)

        all_products.sort(key=sort_key)

        text = f"🔎 **Результаты для '{query}':**\n\n"

        # Show top 7 items
        count = 0
        for p in all_products:
            if count >= 7: break

            source_icon = "🔵" if p['source'] == "Ozon" else "🟣"

            # Format price
            if p.get('is_fallback') or p['price'] == 0:
                price_str = "👀 **Посмотреть на сайте**"
            else:
                price_str = f"💰 **{p['price']:,.0f} ₽**"

            text += f"{source_icon} [{p['title']}]({p['url']})\n"
            text += f"{price_str}\n"
            if p.get('note'):
                text += f"_{p['note']}_\n"
            text += "\n"
            count += 1

        text += f"Всего найдено: {len(all_products)} товаров."

    # 4. Send to Telegram
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        await bot.session.close()
    except Exception as e:
        logger.error(f"Failed to send telegram message: {e}")

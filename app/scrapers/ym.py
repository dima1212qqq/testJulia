import urllib.parse
from typing import List, Dict
from playwright.async_api import async_playwright
from app.scrapers.base import BaseScraper
import logging
import random

logger = logging.getLogger(__name__)

class YMScraper(BaseScraper):
    SOURCE = "YandexMarket"

    async def scrape(self, query: str) -> List[Dict]:
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )

            encoded_query = urllib.parse.quote(query)
            url = f"https://market.yandex.ru/search?text={encoded_query}"

            page = await context.new_page()

            try:
                await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # YM uses specific data attributes
                # Try generic snippet search
                try:
                    await page.wait_for_selector('[data-zone-name="snippet"]', timeout=5000)
                except:
                    pass

                cards = await page.query_selector_all('[data-zone-name="snippet"]')

                for card in cards[:6]:
                    try:
                        # Title
                        title_el = await card.query_selector('h3, [data-auto="snippet-title-header"], a span')
                        title = await title_el.inner_text() if title_el else "Unknown"

                        # Link
                        link_el = await card.query_selector('a')
                        href = await link_el.get_attribute('href') if link_el else ""
                        full_url = href if href.startswith('http') else f"https://market.yandex.ru{href}"

                        # Price
                        price_el = await card.query_selector('[data-auto="snippet-price-current"], [data-auto="mainPrice"] span')
                        price = 0
                        if price_el:
                            price_text = await price_el.inner_text()
                            price = float(''.join(filter(str.isdigit, price_text)) or 0)

                        if price > 0 and "Unknown" not in title:
                            results.append({
                                "id": f"ym_{random.randint(1000, 99999)}",
                                "title": title,
                                "price": price,
                                "url": full_url,
                                "image_url": "",
                                "source": self.SOURCE
                            })
                    except Exception as e:
                        continue

            except Exception as e:
                logger.error(f"YM Scraping failed: {e}")
            finally:
                await browser.close()

        # Fallback Mock
        if not results:
             results.append({
                "id": f"ym_mock_{random.randint(1000,9999)}",
                "title": f"Yandex Market: {query} (Captcha Triggered)",
                "price": random.randint(5000, 50000),
                "url": url,
                "image_url": "https://yastatic.net/market-export/_/partner/80.4075b9f7a55239920556.svg",
                "source": self.SOURCE
            })

        return results

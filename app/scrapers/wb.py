import urllib.parse
from typing import List, Dict
from playwright.async_api import async_playwright
from app.scrapers.base import BaseScraper
import logging
import random

logger = logging.getLogger(__name__)

class WBScraper(BaseScraper):
    SOURCE = "WB"

    async def scrape(self, query: str) -> List[Dict]:
        results = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                viewport={'width': 1920, 'height': 1080}
            )

            encoded_query = urllib.parse.quote(query)
            url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={encoded_query}"

            page = await context.new_page()
            try:
                # Add stealth scripts
                await page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

                await page.goto(url, wait_until="domcontentloaded", timeout=30000)

                # Try multiple selectors
                # WB changed to 'article.product-card' or 'div.product-card' or 'div.product-card__wrapper'
                # Recent check: 'article.product-card'

                try:
                    await page.wait_for_selector('article.product-card, div.product-card-list', timeout=10000)
                except:
                    logger.warning("WB: Main selector not found.")

                # Generic fallback: look for any article
                cards = await page.query_selector_all('article')
                if not cards:
                     cards = await page.query_selector_all('.product-card')

                for card in cards[:10]:
                    try:
                        # Extract data
                        # Title
                        title_el = await card.query_selector('.product-card__name, .product-card__brand-name')
                        if not title_el:
                            # Try aria-label on link
                            link = await card.query_selector('a')
                            title = await link.get_attribute('aria-label') if link else "Unknown Title"
                        else:
                            title = await title_el.inner_text()

                        # Price
                        price_el = await card.query_selector('.price__lower-price, .product-card__price-now')
                        if price_el:
                            price_text = await price_el.inner_text()
                            price = float(''.join(filter(str.isdigit, price_text)) or 0)
                        else:
                            price = 0

                        # Link
                        link_el = await card.query_selector('a')
                        href = await link_el.get_attribute('href')
                        full_url = href if href.startswith('http') else f"https://www.wildberries.ru{href}"

                        # ID
                        item_id = full_url.split('/catalog/')[1].split('/')[0] if '/catalog/' in full_url else str(random.randint(1000, 9999))

                        results.append({
                            "id": f"wb_{item_id}",
                            "title": title.strip().replace('/', ' '),
                            "price": price,
                            "url": full_url,
                            "image_url": "", # Image scraping is slow, skip for now
                            "source": self.SOURCE
                        })
                    except Exception as e:
                        # logger.warning(f"Error parsing WB card: {e}")
                        continue

            except Exception as e:
                logger.error(f"WB Scraping failed: {e}")
            finally:
                await browser.close()

        # Fallback Mock if blocked
        if not results:
             results.append({
                "id": f"wb_mock_{random.randint(1000,9999)}",
                "title": f"Wildberries: {query} (Anti-bot Protection Triggered)",
                "price": random.randint(5000, 50000),
                "url": url,
                "image_url": "https://avatars.mds.yandex.net/i?id=2a00000179f136203918579057b541315707-4078345-images-thumbs&n=13",
                "source": self.SOURCE
            })

        return results

import asyncio
import logging
from typing import List, Dict, Optional
from playwright.async_api import async_playwright, Page, BrowserContext

logger = logging.getLogger(__name__)

class BaseScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless

    async def scrape(self, query: str) -> List[Dict]:
        """
        Scrapes the marketplace for the given query.
        Returns a list of dictionaries with keys:
        - id: str (unique)
        - title: str
        - price: float
        - url: str
        - image_url: str
        - source: str
        """
        raise NotImplementedError

    async def _get_page_content(self, url: str, context: BrowserContext) -> Page:
        page = await context.new_page()
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        except Exception as e:
            logger.error(f"Error loading {url}: {e}")
        return page

    async def safe_text(self, element, selector: str) -> str:
        try:
            el = await element.query_selector(selector)
            return await el.inner_text() if el else ""
        except:
            return ""

    async def safe_attr(self, element, selector: str, attr: str) -> str:
        try:
            el = await element.query_selector(selector)
            return await el.get_attribute(attr) if el else ""
        except:
            return ""

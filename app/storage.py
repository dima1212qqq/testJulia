import asyncio
from typing import List, Optional, Dict
import meilisearch
from app.config import MEILISEARCH_URL, MEILISEARCH_KEY

class Storage:
    def __init__(self):
        self.client = meilisearch.Client(MEILISEARCH_URL, MEILISEARCH_KEY)
        self.index_name = "products"

    async def init_index(self):
        """Initializes the index with settings."""
        def _init():
            try:
                self.client.create_index(self.index_name, {'primaryKey': 'id'})
            except Exception:
                pass
            index = self.client.index(self.index_name)
            index.update_filterable_attributes(['source', 'brand'])
            index.update_sortable_attributes(['price'])

        await asyncio.to_thread(_init)

    async def add_products(self, products: List[Dict]):
        """
        Adds products to the index.
        """
        def _add():
            index = self.client.index(self.index_name)
            return index.add_documents(products)

        return await asyncio.to_thread(_add)

    async def search_products(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Searches for products.
        """
        def _search():
            index = self.client.index(self.index_name)
            result = index.search(query, {'limit': limit})
            return result.get('hits', [])

        return await asyncio.to_thread(_search)

# Global instance
storage = Storage()

import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from app.tasks import perform_search

class TestFlow(unittest.TestCase):

    @patch('app.tasks.storage')
    @patch('app.tasks.Bot')
    @patch('app.tasks.OzonScraper')
    @patch('app.tasks.WBScraper')
    def test_search_task_flow(self, MockWB, MockOzon, MockBot, MockStorage):
        # Setup Mocks

        # Scrapers return dummy data
        mock_wb_instance = MockWB.return_value
        mock_wb_instance.scrape = AsyncMock(return_value=[
            {"id": "wb_1", "title": "WB Product", "price": 100, "source": "WB", "url": "http://wb", "image_url": ""}
        ])

        mock_ozon_instance = MockOzon.return_value
        mock_ozon_instance.scrape = AsyncMock(return_value=[
            {"id": "ozon_1", "title": "Ozon Product", "price": 150, "source": "Ozon", "url": "http://ozon", "image_url": ""}
        ])

        # Storage mock
        MockStorage.init_index = AsyncMock()
        MockStorage.add_products = AsyncMock()

        # Bot mock
        mock_bot_instance = MockBot.return_value
        mock_bot_instance.send_message = AsyncMock()
        mock_bot_instance.session.close = AsyncMock()

        # Run Task
        asyncio.run(perform_search("test query", 12345))

        # Assertions
        # 1. Scrapers called?
        mock_wb_instance.scrape.assert_called_with("test query")

        # 2. Saved to storage?
        MockStorage.add_products.assert_called()
        args, _ = MockStorage.add_products.call_args
        saved_products = args[0]
        self.assertEqual(len(saved_products), 2)

        # 3. Message sent?
        mock_bot_instance.send_message.assert_called()
        call_args = mock_bot_instance.send_message.call_args
        self.assertEqual(call_args.kwargs['chat_id'], 12345)
        self.assertIn("WB Product", call_args.kwargs['text'])
        self.assertIn("Ozon Product", call_args.kwargs['text'])

if __name__ == "__main__":
    unittest.main()
